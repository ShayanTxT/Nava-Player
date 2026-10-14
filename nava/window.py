"""Main window + list delegate + tray integration."""
from __future__ import annotations

import base64
import math
import os

from PySide6.QtCore import (QByteArray, QObject, QPoint, QRectF, QRunnable, QSize, Qt,
                            QThread, QThreadPool, QTimer, Signal)
from PySide6.QtGui import (QAction, QActionGroup, QColor, QFont, QFontMetrics, QIcon,
                           QImage, QKeySequence, QPainter, QPainterPath, QPixmap, QShortcut)
from PySide6.QtWidgets import (QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout,
                               QLabel, QLineEdit, QListWidget, QListWidgetItem, QMainWindow,
                               QMenu, QPushButton, QSizePolicy, QSlider, QSplitter,
                               QStackedWidget, QSystemTrayIcon, QVBoxLayout, QWidget)

from . import winutils
from .config import Config
from .i18n import TR
from .icons import app_icon_pixmap, icon_pixmap
from .library import Track, extract_cover, is_audio, read_tags, scan_folder, sort_tracks
from .player import PlayerController
from .theme import QSS as QSS_TEMPLATE, THEMES, THEME_BY_KEY, DEFAULT_THEME, next_theme
from .widgets import CoverWidget, IconButton, SeekSlider

ROW_H = 64


# --------------------------------------------------------------------------- covers
class CoverCache(QObject):
    """Lazy album-art loader: tag/embedded art first, then cover.jpg next to the file."""

    ready = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._bytes: dict[str, bytes | None] = {}
        self._pix: dict[str, QPixmap] = {}
        self._pending: set[str] = set()
        self._pool = QThreadPool()
        self._pool.setMaxThreadCount(2)

    def _load(self, path: str):
        data = extract_cover(path)
        self._bytes[path] = data
        self._pending.discard(path)
        self.ready.emit(path)

    def pixmap(self, path: str, size: int) -> QPixmap | None:
        key = f"{path}|{size}"
        if key in self._pix:
            return self._pix[key]
        if path not in self._bytes and path not in self._pending:
            self._pending.add(path)
            self._pool.start(_CoverTask(self._load, path))
            return None
        data = self._bytes.get(path)
        if not data:
            return None
        pm = QPixmap()
        if not pm.loadFromData(data):
            return None
        pm = pm.scaled(size, size, Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        self._pix[key] = pm
        return pm

    def forget(self, path: str):
        self._bytes.pop(path, None)
        for key in [k for k in self._pix if k.startswith(path + "|")]:
            self._pix.pop(key, None)

    def clear(self):
        self._bytes.clear()
        self._pix.clear()


class _CoverTask(QRunnable):
    def __init__(self, fn, path):
        super().__init__()
        self._fn, self._path = fn, path
        self.setAutoDelete(True)

    def run(self):
        try:
            self._fn(self._path)
        except Exception:
            pass


# ------------------------------------------------------------------------ delegate
class TrackDelegate(QWidget):
    """Paints the library rows: art thumb, title/artist, duration, playing equalizer."""

    def __init__(self, owner: "MainWindow"):
        super().__init__()
        self.owner = owner
        self._phase = 0.0
        self._hover_row = -1

    def advance(self):
        self._phase += 0.55
        self.update()

    # -- helpers ---------------------------------------------------------
    def _colors(self):
        t = self.owner.theme
        return t

    def paint_row(self, painter: QPainter, rect, track: Track, selected: bool,
                  hovered: bool, playing: bool, theme):
        painter.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(rect).adjusted(2, 3, -2, -3)

        if playing or selected or hovered:
            path = QPainterPath()
            path.addRoundedRect(r, 13, 13)
            if playing:
                painter.fillPath(path, _alpha(theme.accent, 30))
                painter.setPen(theme.accent)
            elif selected:
                painter.fillPath(path, _alpha(theme.accent, 20))
                painter.setPen(theme.border)
            else:
                painter.fillPath(path, _alpha(theme.text, 10))
                painter.setPen(Qt.NoPen)
            painter.setBrush(Qt.NoBrush)
            painter.drawPath(path)

        # --- album art thumbnail ---
        art_size = ROW_H - 22
        art_rect = r.adjusted(9, 0, 0, 0)
        art_rect.setWidth(art_size)
        art_rect.setHeight(art_size)
        art_rect.moveTop(r.top() + (r.height() - art_size) / 2)
        art_path = QPainterPath()
        art_path.addRoundedRect(art_rect, 10, 10)
        pm = self.owner.covers.pixmap(track.path, art_size * 2)
        if pm is not None:
            painter.save()
            painter.setClipPath(art_path)
            scaled = pm.scaled(art_size * 2, art_size * 2, Qt.KeepAspectRatioByExpanding,
                               Qt.SmoothTransformation)
            painter.drawPixmap(art_rect.toRect(), scaled)
            painter.restore()
        else:
            painter.fillPath(art_path, _alpha(theme.accent, 34))
            note = icon_pixmap("note", theme.accent, art_size - 14, 1.8,
                               self.devicePixelRatioF())
            painter.drawPixmap(int(art_rect.center().x() - (art_size - 14) / 2),
                               int(art_rect.center().y() - (art_size - 14) / 2), note)

        # --- texts ---
        text_left = art_rect.right() + 12
        right_pad = 14
        right_reserved = 74
        avail = max(60, r.right() - right_pad - right_reserved - text_left)

        font = QFont(self.font())
        font.setPointSizeF(10.2)
        font.setBold(True)
        painter.setFont(font)
        fm = QFontMetrics(font)
        title = fm.elidedText(track.display_title, Qt.ElideRight, int(avail))
        painter.setPen(theme.accent if playing else theme.text)
        painter.drawText(int(text_left), int(r.center().y() - 2), title)

        font2 = QFont(self.font())
        font2.setPointSizeF(9.0)
        painter.setFont(font2)
        fm2 = QFontMetrics(font2)
        sub = track.artist or TR("unknown_artist")
        if track.album:
            sub = f"{sub}  ·  {track.album}"
        sub = fm2.elidedText(sub, Qt.ElideRight, int(avail))
        painter.setPen(theme.dim)
        painter.drawText(int(text_left), int(r.center().y() + 15), sub)

        # --- duration / equalizer ---
        font3 = QFont(self.font())
        font3.setPointSizeF(9.0)
        painter.setFont(font3)
        painter.setPen(theme.dim)
        dur_rect = r.adjusted(0, 0, -right_pad, 0)
        dur_rect.setLeft(dur_rect.right() - 62)
        if playing:
            dur_rect.setRight(dur_rect.right() - 26)
        painter.drawText(dur_rect, Qt.AlignVCenter | Qt.AlignRight, track.duration_text)

        if playing:
            bars_x = r.right() - right_pad - 18
            base_y = r.center().y() + 11
            for i in range(4):
                h = 4 + 11 * abs(math.sin(self._phase * 0.9 + i * 0.8))
                path2 = QPainterPath()
                path2.addRoundedRect(bars_x + i * 4.5, base_y - h, 2.6, h, 1.3, 1.3)
                painter.fillPath(path2, _alpha(theme.accent, 235))

        return art_rect


def _hex_alpha(color_hex: str, alpha: int) -> str:
    c = QColor(color_hex)
    return f"#{max(0, min(255, int(alpha))):02x}{c.red():02x}{c.green():02x}{c.blue():02x}"


def _alpha(color_hex: str, alpha: int):
    c = QColor(color_hex)
    c.setAlpha(alpha)
    return c


# -------------------------------------------------------------------------- list
class MediaList(QListWidget):
    """List widget with a custom-painted, cozy row style."""

    play_requested = Signal(int)          # index into the library
    context_requested = Signal(int, QPoint)

    def __init__(self, owner: "MainWindow"):
        super().__init__(owner)
        self.owner = owner
        self.delegate = TrackDelegate(owner)
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QListWidget.ScrollPerPixel)
        self.setSelectionMode(QListWidget.SingleSelection)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFrameShape(QFrame.NoFrame)
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self._ctx)
        self.itemDoubleClicked.connect(lambda item: self.play_requested.emit(item.data(Qt.UserRole)))
        self.itemClicked.connect(lambda item: self.play_requested.emit(item.data(Qt.UserRole)))
        self._hover_row = -1

    # painting ------------------------------------------------------------
    def paintEvent(self, event):
        painter = QPainter(self.viewport())
        theme = self.owner.theme
        current = self.owner.player.current
        current_key = current.key() if current is not None else ""
        viewport_rect = event.rect()

        for row in range(self.count()):
            item = self.item(row)
            row_rect = self.visualItemRect(item)
            if not row_rect.intersects(viewport_rect):
                continue
            index = item.data(Qt.UserRole)
            if index is None or index >= len(self.owner.tracks):
                continue
            track = self.owner.tracks[index]
            playing = bool(current_key) and track.key() == current_key
            selected = item.isSelected()
            hovered = row == self._hover_row
            self.delegate.paint_row(painter, QRectF(row_rect), track, selected, hovered, playing, theme)
        painter.end()

    def sizeHintForRow(self, row: int) -> int:
        return ROW_H

    # interaction ---------------------------------------------------------
    def mouseMoveEvent(self, event):
        item = self.itemAt(event.position().toPoint())
        row = self.row(item) if item is not None else -1
        if row != self._hover_row:
            old = self._hover_row
            self._hover_row = row
            if old >= 0 and old < self.count():
                self.viewport().update(self.visualItemRect(self.item(old)))
            if row >= 0:
                self.viewport().update(self.visualItemRect(self.item(row)))
        super().mouseMoveEvent(event)

    def leaveEvent(self, event):
        if self._hover_row >= 0 and self._hover_row < self.count():
            self.viewport().update(self.visualItemRect(self.item(self._hover_row)))
        self._hover_row = -1
        super().leaveEvent(event)

    def _ctx(self, point: QPoint):
        item = self.itemAt(point)
        if item is None:
            return
        index = item.data(Qt.UserRole)
        if index is not None:
            self.context_requested.emit(index, self.viewport().mapToGlobal(point))

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key_Return, Qt.Key_Enter) and self.currentItem() is not None:
            self.play_requested.emit(self.currentItem().data(Qt.UserRole))
            return
        super().keyPressEvent(event)

    def update_row_of(self, track: Track | None):
        """Repaint just the row showing this track."""
        if track is None:
            self.viewport().update()
            return
        for row in range(self.count()):
            index = self.item(row).data(Qt.UserRole)
            if index is not None and index < len(self.owner.tracks) \
                    and self.owner.tracks[index].key() == track.key():
                self.viewport().update(self.visualItemRect(self.item(row)))
                return


# ------------------------------------------------------------------- scanning
class FolderScanner(QThread):
    batch = Signal(list)
    finished_scan = Signal(int)
    failed = Signal(str)

    def __init__(self, folder: str, recursive: bool, parent=None):
        super().__init__(parent)
        self.folder = folder
        self.recursive = recursive
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        try:
            count = scan_folder(
                self.folder, self.recursive, batch_size=60,
                should_stop=lambda: self._stop,
                on_batch=lambda batch: self.batch.emit(list(batch)))
            self.finished_scan.emit(count)
        except Exception as exc:            # pragma: no cover - defensive
            self.failed.emit(str(exc))


# ------------------------------------------------------------------- main window
class MainWindow(QMainWindow):
    def __init__(self, cfg: Config | None = None):
        super().__init__()
        self.cfg = cfg or Config()
        TR.set_lang(self.cfg["lang"])
        self.setLayoutDirection(Qt.RightToLeft if self.cfg["lang"] == "fa" else Qt.LeftToRight)

        self.tracks: list[Track] = []
        self.view: list[int] = []                 # visible library indices (after search)
        self.covers = CoverCache(self)
        self.player = PlayerController(self)
        self.theme = THEME_BY_KEY.get(self.cfg["theme"], DEFAULT_THEME)
        self.scanner: FolderScanner | None = None
        self._hover_row = -1
        self._spin = 0.0
        self._quitting = False

        self.setWindowTitle(TR("window_title"))
        self.setMinimumSize(QSize(940, 620))
        self.resize(1120, 730)

        self._build_ui()
        self._build_menu()
        self._build_tray()
        self._wire()
        self.apply_theme(self.theme)
        self.retranslate()

        geo = self.cfg.get("geometry")
        if geo:
            try:
                self.restoreGeometry(QByteArray(base64.b64decode(geo)))
            except Exception:
                pass

        self.volume.setValue(int(self.cfg["volume"]))     # keeps slider, label and player in sync
        self.player.set_shuffle(bool(self.cfg["shuffle"]))
        self.player.set_repeat(str(self.cfg["repeat"]))
        self.refresh_list()          # shows the cozy empty state when there is no library

        # art/animation ticker
        self._ticker = QTimer(self)
        self._ticker.setInterval(90)
        self._ticker.timeout.connect(self._tick)
        self._ticker.start()

        # restore last library
        folder = self.cfg.get("folder") or ""
        if folder and os.path.isdir(folder):
            QTimer.singleShot(150, lambda: self.load_folder(folder, first=True))

        self._adapt_layout()
        QTimer.singleShot(600, self._maybe_show_tray_hint)

    # ---------------------------------------------------------------- build
    def _build_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        root.setAcceptDrops(True)
        self.setCentralWidget(root)

        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 14, 16, 14)
        outer.setSpacing(13)

        # ---------- header ----------
        header = QFrame()
        header.setObjectName("Header")
        hl = QHBoxLayout(header)
        hl.setContentsMargins(16, 11, 14, 11)
        hl.setSpacing(11)

        self.logo = QLabel()
        self.logo.setFixedSize(40, 40)
        hl.addWidget(self.logo)

        title_box = QVBoxLayout()
        title_box.setSpacing(0)
        self.lbl_name = QLabel()
        self.lbl_name.setObjectName("AppName")
        self.lbl_tag = QLabel()
        self.lbl_tag.setObjectName("AppTag")
        title_box.addWidget(self.lbl_name)
        title_box.addWidget(self.lbl_tag)
        hl.addLayout(title_box)
        hl.addSpacing(10)

        self.btn_folder = QPushButton()
        self.btn_folder.setObjectName("Accent")
        self.btn_folder.setCursor(Qt.PointingHandCursor)
        self.btn_folder.setMinimumHeight(38)
        self.btn_folder.setMaximumWidth(330)
        hl.addWidget(self.btn_folder)

        self.btn_rescan = IconButton("clock", 38, 19)
        self.btn_theme = IconButton("palette", 38, 19)
        self.btn_pin = IconButton("pin", 38, 19)
        self.btn_menu = IconButton("list", 38, 20)
        for b in (self.btn_rescan, self.btn_theme, self.btn_pin, self.btn_menu):
            hl.addWidget(b)
        hl.addStretch(1)

        outer.addWidget(header)

        # ---------- body ----------
        splitter = QSplitter(Qt.Horizontal)
        splitter.setChildrenCollapsible(False)
        splitter.setHandleWidth(8)

        # left: library
        left = QFrame()
        left.setObjectName("Panel")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(14, 14, 14, 12)
        ll.setSpacing(10)

        self.search = QLineEdit()
        self.search.setClearButtonEnabled(True)
        self.search.setMinimumHeight(38)
        self.search_action = self.search.addAction(QIcon(), QLineEdit.LeadingPosition)
        self.search_action.setEnabled(False)
        ll.addWidget(self.search)

        self.list = MediaList(self)
        self.empty_page = self._build_empty_page()
        self.stack = QStackedWidget()
        self.stack.addWidget(self.list)
        self.stack.addWidget(self.empty_page)
        ll.addWidget(self.stack, 1)

        self.lbl_status = QLabel()
        self.lbl_status.setObjectName("Status")
        ll.addWidget(self.lbl_status)

        # right: now playing
        right = QFrame()
        right.setObjectName("Card")
        rl = QVBoxLayout(right)
        rl.setContentsMargins(20, 20, 20, 16)
        rl.setSpacing(12)

        self.lbl_now = QLabel()
        self.lbl_now.setObjectName("SectionTitle")
        self.lbl_now.setAlignment(Qt.AlignHCenter)
        rl.addWidget(self.lbl_now)

        self.cover = CoverWidget(228)
        rl.addWidget(self.cover, 0, Qt.AlignHCenter)

        self.lbl_title = QLabel()
        self.lbl_title.setObjectName("TrackTitle")
        self.lbl_title.setAlignment(Qt.AlignHCenter)
        self.lbl_title.setWordWrap(True)
        self.lbl_artist = QLabel()
        self.lbl_artist.setObjectName("TrackArtist")
        self.lbl_artist.setAlignment(Qt.AlignHCenter)
        self.lbl_album = QLabel()
        self.lbl_album.setObjectName("TrackAlbum")
        self.lbl_album.setAlignment(Qt.AlignHCenter)
        rl.addWidget(self.lbl_title)
        rl.addWidget(self.lbl_artist)
        rl.addWidget(self.lbl_album)

        self.seek = SeekSlider()
        rl.addWidget(self.seek)

        times = QHBoxLayout()
        self.lbl_pos = QLabel("0:00")
        self.lbl_pos.setObjectName("Time")
        self.lbl_dur = QLabel("0:00")
        self.lbl_dur.setObjectName("Time")
        times.addWidget(self.lbl_pos)
        times.addStretch(1)
        times.addWidget(self.lbl_dur)
        rl.addLayout(times)

        transport = QHBoxLayout()
        transport.setSpacing(6)
        transport.addStretch(1)
        self.btn_shuffle = IconButton("shuffle", 40, 19, checkable=True)
        self.btn_prev = IconButton("prev", 44, 24)
        self.btn_play = IconButton("play", 60, 28, fill=True)
        self.btn_next = IconButton("next", 44, 24)
        self.btn_repeat = IconButton("repeat", 40, 19, checkable=True)
        for b in (self.btn_shuffle, self.btn_prev, self.btn_play, self.btn_next, self.btn_repeat):
            transport.addWidget(b)
        transport.addStretch(1)
        rl.addLayout(transport)

        vol_row = QHBoxLayout()
        vol_row.setSpacing(6)
        self.btn_mute = IconButton("volume", 34, 19)
        self.volume = QSlider(Qt.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setFixedWidth(130)
        self.volume.setCursor(Qt.PointingHandCursor)
        self.lbl_vol = QLabel(f"{int(self.cfg['volume'])}%")
        self.lbl_vol.setObjectName("Time")
        vol_row.addStretch(1)
        vol_row.addWidget(self.btn_mute)
        vol_row.addWidget(self.volume)
        vol_row.addWidget(self.lbl_vol)
        vol_row.addStretch(1)
        rl.addLayout(vol_row)

        rl.addStretch(1)
        self.lbl_hint = QLabel()
        self.lbl_hint.setObjectName("Status")
        self.lbl_hint.setAlignment(Qt.AlignHCenter)
        self.lbl_hint.setWordWrap(True)
        rl.addWidget(self.lbl_hint)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 63)
        splitter.setStretchFactor(1, 37)
        splitter.setSizes([700, 400])
        outer.addWidget(splitter, 1)

        self.setAcceptDrops(True)

    def _build_empty_page(self) -> QWidget:
        page = QWidget()
        v = QVBoxLayout(page)
        v.addStretch(1)
        self.empty_icon = QLabel()
        self.empty_icon.setAlignment(Qt.AlignHCenter)
        v.addWidget(self.empty_icon)
        self.empty_title = QLabel()
        self.empty_title.setAlignment(Qt.AlignHCenter)
        f = QFont(self.font())
        f.setPointSizeF(12.5)
        f.setBold(True)
        self.empty_title.setFont(f)
        v.addSpacing(10)
        v.addWidget(self.empty_title)
        self.empty_hint = QLabel()
        self.empty_hint.setObjectName("Status")
        self.empty_hint.setAlignment(Qt.AlignHCenter)
        self.empty_hint.setWordWrap(True)
        v.addWidget(self.empty_hint)
        v.addSpacing(12)
        row = QHBoxLayout()
        row.addStretch(1)
        self.empty_btn = QPushButton()
        self.empty_btn.setObjectName("Accent")
        self.empty_btn.setCursor(Qt.PointingHandCursor)
        self.empty_btn.setMinimumHeight(40)
        self.empty_btn.setMinimumWidth(180)
        row.addWidget(self.empty_btn)
        row.addStretch(1)
        v.addLayout(row)
        v.addStretch(2)
        return page

    def _build_menu(self):
        self.menu = QMenu(self)

        self.act_folder = QAction(self)
        self.act_rescan = QAction(self)
        self.act_open_folder = QAction(self)
        self.act_recursive = QAction(self)
        self.act_recursive.setCheckable(True)
        self.act_recursive.setChecked(bool(self.cfg["recursive"]))

        self.menu_theme = QMenu(self)
        self.theme_group = QActionGroup(self)
        self.theme_actions = {}
        for theme in THEMES:
            act = QAction(theme.name(TR.lang), self, checkable=True)
            act.setChecked(theme.key == self.theme.key)
            act.triggered.connect(lambda _c=False, k=theme.key: self.set_theme_by_key(k))
            self.theme_group.addAction(act)
            self.menu_theme.addAction(act)
            self.theme_actions[theme.key] = act
        self.act_theme = self.menu_theme.menuAction()

        self.menu_lang = QMenu(self)
        self.lang_group = QActionGroup(self)
        self.act_lang_fa = QAction("فارسی", self, checkable=True)
        self.act_lang_en = QAction("English", self, checkable=True)
        self.act_lang_fa.setChecked(TR.lang == "fa")
        self.act_lang_en.setChecked(TR.lang == "en")
        self.act_lang_fa.triggered.connect(lambda: self.set_lang("fa"))
        self.act_lang_en.triggered.connect(lambda: self.set_lang("en"))
        for act in (self.act_lang_fa, self.act_lang_en):
            self.lang_group.addAction(act)
            self.menu_lang.addAction(act)
        self.act_lang = self.menu_lang.menuAction()

        self.act_top = QAction(self, checkable=True)
        self.act_top.setChecked(bool(self.cfg["always_on_top"]))
        self.act_top.triggered.connect(self.set_always_on_top)

        self.act_tray = QAction(self, checkable=True)
        self.act_tray.setChecked(bool(self.cfg["minimize_to_tray"]))
        self.act_tray.triggered.connect(self.set_minimize_to_tray)

        self.act_autostart = QAction(self, checkable=True)
        self.act_autostart.setChecked(winutils.autostart_enabled())
        self.act_autostart.triggered.connect(self.set_autostart)

        self.act_about = QAction(self)
        self.act_about.triggered.connect(self.show_about)

        self.act_quit = QAction(self)
        self.act_quit.triggered.connect(self.quit_app)

        for act in (self.act_folder, self.act_rescan, self.act_open_folder):
            self.menu.addAction(act)
        self.menu.addAction(self.act_recursive)
        self.menu.addSeparator()
        self.menu.addAction(self.act_theme)
        self.menu.addAction(self.act_lang)
        self.menu.addSeparator()
        self.menu.addAction(self.act_top)
        self.menu.addAction(self.act_tray)
        self.menu.addAction(self.act_autostart)
        self.menu.addSeparator()
        self.menu.addAction(self.act_about)
        self.menu.addSeparator()
        self.menu.addAction(self.act_quit)

        self.act_folder.triggered.connect(self.choose_folder)
        self.act_rescan.triggered.connect(lambda: self.load_folder(self.cfg.get("folder"), first=False))
        self.act_open_folder.triggered.connect(self.open_folder_in_explorer)
        self.act_recursive.triggered.connect(self._toggle_recursive)

    def _build_tray(self):
        self.tray = None
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return
        self.tray = QSystemTrayIcon(self)
        self.tray.setIcon(self._make_icon())
        self.tray_menu = QMenu()
        self.tray_show = QAction(self)
        self.tray_np = QAction(self)
        self.tray_np.setEnabled(False)
        self.tray_toggle = QAction(self)
        self.tray_next = QAction(self)
        self.tray_prev = QAction(self)
        self.tray_quit = QAction(self)
        for act in (self.tray_show, self.tray_np, self.tray_toggle, self.tray_prev,
                    self.tray_next, self.tray_quit):
            self.tray_menu.addAction(act)
            if act in (self.tray_np,):
                self.tray_menu.addSeparator()
        self.tray_show.triggered.connect(self.toggle_window)
        self.tray_toggle.triggered.connect(self.player.toggle)
        self.tray_next.triggered.connect(lambda: self.player.next())
        self.tray_prev.triggered.connect(self.player.prev)
        self.tray_quit.triggered.connect(self.quit_app)
        self.tray.setContextMenu(self.tray_menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()

    def _make_icon(self, color: str | None = None) -> QIcon:
        icon = QIcon()
        for size in (16, 20, 24, 32, 48, 64, 128, 256):
            icon.addPixmap(app_icon_pixmap(size, self.theme.accent, self.theme.accent2,
                                           self.theme.on_accent))
        return icon

    # ----------------------------------------------------------------- wire
    def _wire(self):
        self.btn_folder.clicked.connect(self.choose_folder)
        self.empty_btn.clicked.connect(self.choose_folder)
        self.btn_rescan.clicked.connect(lambda: self.load_folder(self.cfg.get("folder"), first=False))
        self.btn_theme.clicked.connect(self.cycle_theme)
        self.btn_pin.clicked.connect(lambda: self.set_always_on_top(self.btn_pin.isChecked()))
        self.btn_menu.clicked.connect(self._show_main_menu)
        self.btn_folder.setContextMenuPolicy(Qt.CustomContextMenu)
        self.btn_folder.customContextMenuRequested.connect(
            lambda pos: self.menu.exec(self.btn_folder.mapToGlobal(pos)))

        self.search.textChanged.connect(lambda _t: self.refresh_list(preserve_scroll=True))
        self.search.returnPressed.connect(self._play_first_result)

        self.list.play_requested.connect(self.play_library_index)
        self.list.context_requested.connect(self._track_menu)

        self.btn_play.clicked.connect(self.player.toggle)
        self.btn_next.clicked.connect(lambda: self.player.next())
        self.btn_prev.clicked.connect(self.player.prev)
        self.btn_shuffle.clicked.connect(lambda: self.player.set_shuffle(self.btn_shuffle.isChecked()))
        self.btn_repeat.clicked.connect(self._cycle_repeat)
        self.btn_mute.clicked.connect(self._toggle_mute)
        self.volume.valueChanged.connect(self._on_volume)
        self.volume.sliderReleased.connect(self.cfg.save)
        self.seek.valueChanged.connect(self._on_seek)

        self.player.track_changed.connect(self._on_track_changed)
        self.player.playing_changed.connect(self._on_playing_changed)
        self.player.position_changed.connect(self._on_position)
        self.player.duration_changed.connect(self._on_duration)
        self.player.error.connect(self._on_error)
        self.player.repeat_changed.connect(lambda _m: self._sync_repeat_icon())
        self.player.shuffle_changed.connect(lambda v: self.btn_shuffle.setChecked(v))
        self.covers.ready.connect(self._on_cover_ready)

        self._shortcuts = []
        for keys, slot in (
            (("Ctrl+O",), self.choose_folder),
            (("Ctrl+F",), lambda: self.search.setFocus()),
            (("Ctrl+S",), lambda: self.btn_shuffle.clicked.emit()),
            (("Ctrl+R",), self._cycle_repeat),
            (("Ctrl+Q",), self.quit_app),
            (("Media Play", "MediaPlay"), self.player.toggle),
            (("Media Next", "MediaNext"), lambda: self.player.next()),
            (("Media Previous", "MediaPrevious"), self.player.prev),
            (("Ctrl+Right",), lambda: self._seek_by(5000)),
            (("Ctrl+Left",), lambda: self._seek_by(-5000)),
        ):
            for key in keys:
                try:
                    sc = QShortcut(QKeySequence(key), self)
                    sc.setContext(Qt.ApplicationShortcut)
                    sc.activated.connect(slot)
                    self._shortcuts.append(sc)
                    break
                except Exception:
                    continue

    # ------------------------------------------------------------- theming
    def apply_theme(self, theme):
        self.theme = theme
        self.cfg["theme"] = theme.key
        qss = QSS_TEMPLATE.substitute(
            bg=theme.bg, bg2=theme.bg2, panel=theme.panel, panel2=theme.panel2,
            border=theme.border, text=theme.text, dim=theme.dim, accent=theme.accent,
            accent2=theme.accent2, on_accent=theme.on_accent)
        self.setStyleSheet(qss)
        app = QApplication.instance()
        if app is not None:
            app.setStyleSheet(qss)      # so menus/tooltips outside the window are themed too
        self.covers.clear()
        self.list.viewport().update()
        self.cover.set_theme(theme)
        for b in (self.btn_folder, self.empty_btn):
            b.setIcon(QIcon(icon_pixmap("folder", theme.on_accent, 18, 2.0,
                                        self.devicePixelRatioF())))
        self.logo.setPixmap(app_icon_pixmap(40, theme.accent, theme.accent2,
                                           theme.on_accent, self.devicePixelRatioF()))
        self.empty_icon.setPixmap(icon_pixmap("folder", _hex_alpha(theme.accent, 190), 66, 1.5,
                                              self.devicePixelRatioF()))
        for b in (self.btn_rescan, self.btn_theme, self.btn_pin, self.btn_menu, self.btn_shuffle,
                  self.btn_prev, self.btn_play, self.btn_next, self.btn_repeat, self.btn_mute):
            b.set_theme(theme)
        self.search_action.setIcon(QIcon(icon_pixmap("search", theme.dim, 17, 1.9,
                                                     self.devicePixelRatioF())))
        if self.tray is not None:
            self.tray.setIcon(self._make_icon())
        for key, act in self.theme_actions.items():
            act.setChecked(key == theme.key)
        self.cfg.save()

    def set_theme_by_key(self, key: str):
        theme = THEME_BY_KEY.get(key)
        if theme is not None:
            self.apply_theme(theme)

    def cycle_theme(self):
        self.apply_theme(next_theme(self.theme.key))
        self.status_text(TR("theme_name", name=self.theme.name(TR.lang)), 2500)

    # ------------------------------------------------------------ language
    def set_lang(self, lang: str):
        TR.set_lang(lang)
        self.cfg["lang"] = lang
        # mirror the whole interface for Persian, natural LTR for English
        self.setLayoutDirection(Qt.RightToLeft if lang == "fa" else Qt.LeftToRight)
        self.search.setLayoutDirection(Qt.RightToLeft if lang == "fa" else Qt.LeftToRight)
        self.act_lang_fa.setChecked(lang == "fa")
        self.act_lang_en.setChecked(lang == "en")
        for theme in THEMES:
            self.theme_actions[theme.key].setText(theme.name(lang))
        self.setWindowTitle(TR("window_title"))
        self.retranslate()
        self.refresh_list()
        current = self.player.current
        self._update_track_labels(current)
        self.cfg.save()

    def retranslate(self):
        self.lbl_name.setText(TR("app_name"))
        self.lbl_tag.setText(TR("app_tagline"))
        self.btn_folder.setText(self._folder_chip_text())
        self.btn_folder.setToolTip(self.cfg.get("folder") or TR("choose_folder"))
        self.empty_title.setText(TR("empty_library"))
        self.empty_hint.setText(TR("empty_library_hint"))
        self.empty_btn.setText(TR("choose_folder"))
        self.lbl_now.setText(TR("now_playing").upper() if TR.lang == "en" else TR("now_playing"))
        self.search.setPlaceholderText(TR("search_placeholder"))
        self.act_recursive.setChecked(bool(self.cfg["recursive"]))
        self.lbl_hint.setText(TR("hint_shortcuts"))
        self.btn_rescan.setToolTip(TR("scanning") if self.scanner else TR("change_folder"))
        self.btn_theme.setToolTip(TR("theme"))
        self.btn_pin.setToolTip(TR("always_on_top"))
        self.btn_menu.setToolTip(TR("menu"))
        self.btn_shuffle.setToolTip(TR("shuffle"))
        self.btn_prev.setToolTip(TR("prev"))
        self.btn_play.setToolTip(TR("play"))
        self.btn_next.setToolTip(TR("next"))
        self.btn_mute.setToolTip(TR("mute"))
        self.act_folder.setText(TR("choose_folder"))
        self.act_rescan.setText(TR("change_folder"))
        self.act_open_folder.setText(TR("open_in_explorer"))
        self.act_recursive.setText(TR("include_subfolders"))
        self.act_theme.setText(TR("theme"))
        self.act_lang.setText(TR("language"))
        self.act_top.setText(TR("always_on_top"))
        self.act_tray.setText(TR("close_to_tray"))
        self.act_autostart.setText(TR("autostart"))
        self.act_about.setText(TR("about"))
        self.act_quit.setText(TR("quit"))
        if self.tray is not None:
            self.tray_show.setText(TR("show_window") if not self.isVisible() else TR("hide_window"))
            self.tray_toggle.setText(TR("pause") if self.player.is_playing else TR("play"))
            self.tray_next.setText(TR("next"))
            self.tray_prev.setText(TR("prev"))
            self.tray_quit.setText(TR("quit"))
            if self.player.current is not None:
                self.tray_np.setText(TR("now_playing_tray", t=self.player.current.display_title))
        if self.player.current is None:
            self.lbl_title.setText(TR("nothing_playing"))
            self.lbl_artist.setText(TR("pick_a_song"))
            self.lbl_album.setText("")
        self._sync_repeat_icon()
        self._update_status()

    # ------------------------------------------------------------- library
    def choose_folder(self):
        start = self.cfg.get("folder") or os.path.expanduser("~")
        folder = QFileDialog.getExistingDirectory(self, TR("choose_folder"), start,
                                                  QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)
        if folder:
            self.load_folder(folder, first=False)

    def load_folder(self, folder: str | None, first: bool = False):
        if not folder:
            return
        if not os.path.isdir(folder):
            self.status_text(TR("folder_missing"), 3200)
            return

        if self.scanner is not None and self.scanner.isRunning():
            self.scanner.stop()
            self.scanner.wait(1500)

        self.cfg["folder"] = folder
        self.cfg.save()

        self.tracks = []
        self.player.stop()
        self.player.set_queue([], autoplay=False)
        self.covers.clear()
        self.refresh_list()
        self._update_status(scanning=True)
        self.btn_folder.setText(self._folder_chip_text())

        self.scanner = FolderScanner(folder, bool(self.cfg["recursive"]), self)
        self.scanner.batch.connect(self._on_scan_batch)
        self.scanner.finished_scan.connect(lambda n: self._on_scan_done(n, folder, first))
        self.scanner.failed.connect(self._on_scan_failed)
        self.scanner.start()

    def _on_scan_batch(self, batch: list[Track]):
        self.tracks.extend(batch)
        self.refresh_list(preserve_scroll=True)
        self._update_status(scanning=True)

    def _on_scan_done(self, count: int, folder: str, first: bool):
        self.tracks = sort_tracks(self.tracks)
        self.refresh_list()
        self._update_status()
        name = os.path.basename(os.path.normpath(folder))
        if count == 0:
            self.status_text(TR("folder_empty"), 4000)
        else:
            self.status_text(TR("folder_loaded", n=count, name=name), 4000)

        # restore the last played track if it belongs to this folder
        if first:
            key = self.cfg.get("last_index")
            tracks = self.tracks
            if tracks and isinstance(key, int) and 0 <= key < len(tracks):
                self._select_row_of(tracks[key])

    def _on_scan_failed(self, message: str):
        self.status_text(f"{TR('scan_error')}: {message}", 5000)
        self._update_status()

    def _toggle_recursive(self, checked: bool):
        self.cfg["recursive"] = bool(checked)
        self.cfg.save()
        if self.cfg.get("folder"):
            self.load_folder(self.cfg["folder"])

    # ----------------------------------------------------------- list view
    def refresh_list(self, preserve_scroll: bool = False):
        query = (self.search.text() or "").strip().lower()
        scroll = self.list.verticalScrollBar().value()
        self.view = []
        for i, track in enumerate(self.tracks):
            if query:
                haystack = f"{track.display_title} {track.artist} {track.album} {track.name}".lower()
                if query not in haystack:
                    continue
            self.view.append(i)

        self.list.setUpdatesEnabled(False)
        self.list.clear()
        for index in self.view:
            track = self.tracks[index]
            item = QListWidgetItem()
            item.setData(Qt.UserRole, index)
            item.setSizeHint(QSize(10, ROW_H))
            self.list.addItem(item)
        self.list.setUpdatesEnabled(True)

        if preserve_scroll:
            self.list.verticalScrollBar().setValue(scroll)
        self._update_status()
        if not self.tracks:
            self.stack.setCurrentWidget(self.empty_page)
        else:
            self.stack.setCurrentWidget(self.list)

    def _play_first_result(self):
        if self.view:
            self.play_library_index(self.view[0])

    def play_library_index(self, index: int):
        if index is None or index < 0 or index >= len(self.tracks):
            return
        queue = [self.tracks[i] for i in self.view] if self.view else list(self.tracks)
        track = self.tracks[index]
        try:
            start = next(i for i, t in enumerate(queue) if t.path == track.path)
        except StopIteration:
            queue = list(self.tracks)
            start = index
        self.player.set_queue(queue, start, autoplay=True)
        try:
            self.cfg["last_index"] = index
        except Exception:
            pass

    def _select_row_of(self, track: Track):
        for row in range(self.list.count()):
            item = self.list.item(row)
            index = item.data(Qt.UserRole)
            if index is not None and index < len(self.tracks) \
                    and self.tracks[index].key() == track.key():
                self.list.setCurrentItem(item)
                self.list.scrollToItem(item, QListWidget.PositionAtCenter)
                return

    def _track_menu(self, index: int, global_pos: QPoint):
        if index < 0 or index >= len(self.tracks):
            return
        track = self.tracks[index]
        menu = QMenu(self)
        act_play = menu.addAction(TR("play_now"))
        act_show = menu.addAction(TR("open_in_explorer"))
        menu.addSeparator()
        act_remove = menu.addAction(TR("remove_from_list"))
        chosen = menu.exec(global_pos)
        if chosen == act_play:
            self.play_library_index(index)
        elif chosen == act_show:
            self.reveal_in_explorer(track.path)
        elif chosen == act_remove:
            self.tracks.pop(index)
            self.covers.forget(track.path)
            self.refresh_list()

    def reveal_in_explorer(self, path: str):
        import subprocess
        import sys
        try:
            if sys.platform.startswith("win"):
                subprocess.Popen(["explorer", "/select,", os.path.normpath(path)])
            else:
                subprocess.Popen(["xdg-open", os.path.dirname(path)])
        except Exception:
            pass

    def open_folder_in_explorer(self):
        folder = self.cfg.get("folder")
        if folder and os.path.isdir(folder):
            self.reveal_in_explorer(os.path.join(folder, ""))

    # ------------------------------------------------------------- player
    def _on_track_changed(self, track: Track | None):
        self._update_track_labels(track)
        self.list.update_row_of(track)
        self.list.viewport().update()
        if track is not None:
            self.cover.set_image(None)
            self._load_cover_for(track)
            self._select_row_of(track)
            self.cfg["last_index"] = next(
                (i for i, t in enumerate(self.tracks) if t.key() == track.key()),
                self.cfg.get("last_index"))
            if self.tray is not None:
                self.tray.setToolTip(TR("now_playing_tray", t=track.display_title))
        if self.tray is not None:
            self.tray_np.setText(TR("now_playing_tray", t=track.display_title) if track
                                 else TR("nothing_playing"))

    def _load_cover_for(self, track: Track):
        """Artwork is read in a worker thread; cached bytes are applied instantly."""
        if track is None:
            self.cover.set_image(None)
            return
        data = self.covers._bytes.get(track.path)
        if data is None:                       # not read yet -> ask the cache to load it
            self.covers.pixmap(track.path, self.cover.width())
            return
        if not data:
            self.cover.set_image(None)
            return
        image = QImage()
        if image.loadFromData(data):
            self.cover.set_image(image)

    def _on_cover_ready(self, path: str):
        self.list.viewport().update()
        track = self.player.current
        if track is not None and track.path == path:
            self._load_cover_for(track)

    def _update_track_labels(self, track: Track | None):
        if track is None:
            self.lbl_title.setText(TR("nothing_playing"))
            self.lbl_artist.setText(TR("pick_a_song"))
            self.lbl_album.setText("")
            self.lbl_dur.setText("0:00")
            self.lbl_pos.setText("0:00")
            self.seek.set_duration(0)
            self.seek.setValue(0)
            return
        self.lbl_title.setText(track.display_title)
        self.lbl_artist.setText(track.artist or TR("unknown_artist"))
        bits = []
        if track.album:
            bits.append(track.album)
        bits.append((track.ext.lstrip(".") or "?").upper())
        self.lbl_album.setText("  ·  ".join(bits))
        self.lbl_dur.setText(track.duration_text)
        self.seek.set_duration(track.duration)

    def _on_playing_changed(self, playing: bool):
        self.btn_play.set_icon("pause" if playing else "play")
        self.cover.set_playing(playing)
        if self.tray is not None:
            self.tray_toggle.setText(TR("pause") if playing else TR("play"))

    def _on_position(self, ms: int):
        self.lbl_pos.setText(_fmt_time(ms / 1000.0))
        if not self.seek.isSliderDown():
            self.seek.blockSignals(True)
            self.seek.setValue(int(ms / max(1, self.player.duration() or 1) * 1000))
            self.seek.blockSignals(False)

    def _on_duration(self, ms: int):
        self.lbl_dur.setText(_fmt_time(ms / 1000.0))
        self.seek.set_duration(ms / 1000.0)

    def _on_seek(self, value: int):
        duration = self.player.duration()
        if duration > 0:
            self.player.set_position(int(duration * value / 1000))

    def _seek_by(self, delta_ms: int):
        pos = max(0, min(self.player.duration() or 0, self.player.position() + delta_ms))
        self.player.set_position(pos)

    def _on_volume(self, value: int):
        self.player.set_volume(value)
        self.lbl_vol.setText(f"{value}%")
        self.btn_mute.set_icon("mute" if value == 0 else
                               ("volume_low" if value < 45 else "volume"))
        self.cfg["volume"] = value
        if not self.volume.isSliderDown():
            self.cfg.save()

    def _toggle_mute(self):
        muted = not self.player.is_muted()
        self.player.set_muted(muted)
        if muted:
            self.btn_mute.set_icon("mute")
            self.btn_mute.set_active(True)
        else:
            self.btn_mute.set_active(False)
            self._on_volume(self.volume.value())

    def _cycle_repeat(self):
        mode = self.player.cycle_repeat()
        self._sync_repeat_icon()
        self.cfg["repeat"] = mode
        text = {"off": TR("repeat_off"), "all": TR("repeat_all"), "one": TR("repeat_one")}[mode]
        self.status_text(text, 1800)

    def _sync_repeat_icon(self):
        mode = self.player.repeat() if hasattr(self, "player") else "off"
        self.btn_repeat.set_icon({"off": "repeat", "all": "repeat",
                                  "one": "repeat_one"}[mode])
        self.btn_repeat.set_active(mode != "off")
        self.btn_repeat.setChecked(mode != "off")
        self.btn_repeat.setToolTip({"off": TR("repeat_off"), "all": TR("repeat_all"),
                                    "one": TR("repeat_one")}[mode])

    def _on_error(self, message: str):
        self._errors_shown = getattr(self, "_errors_shown", 0) + 1
        if self._errors_shown <= 3:
            self.status_text(TR("file_missing", name=os.path.basename(message)), 4200)

    # ------------------------------------------------------------ interactions
    def _show_main_menu(self):
        pos = self.btn_menu.mapToGlobal(QPoint(0, self.btn_menu.height() + 4))
        self.menu.exec(pos)

    def _maybe_show_tray_hint(self):
        if self.tray is None or self.cfg.get("tray_hint_shown"):
            return
        self.cfg["tray_hint_shown"] = True
        self.cfg.save()
        self.tray.showMessage(TR("app_name"), TR("tray_hint"),
                              QSystemTrayIcon.Information, 6000)

    def _tray_activated(self, reason):
        if reason in (QSystemTrayIcon.Trigger, QSystemTrayIcon.DoubleClick):
            self.toggle_window()

    def toggle_window(self):
        if self.isVisible() and not self.isMinimized():
            self.hide()
        else:
            self.showNormal()
            self.raise_()
            self.activateWindow()
        self.retranslate()

    def set_always_on_top(self, enabled: bool):
        self.cfg["always_on_top"] = bool(enabled)
        flags = self.windowFlags()
        if enabled:
            flags |= Qt.WindowStaysOnTopHint
        else:
            flags &= ~Qt.WindowStaysOnTopHint
        was_visible = self.isVisible()
        self.setWindowFlags(flags)
        if was_visible:
            self.show()
        self.btn_pin.set_active(bool(enabled))
        self.btn_pin.setChecked(bool(enabled))
        self.act_top.setChecked(bool(enabled))
        self.cfg.save()

    def set_minimize_to_tray(self, enabled: bool):
        self.cfg["minimize_to_tray"] = bool(enabled)
        self.cfg.save()

    def set_autostart(self, enabled: bool):
        ok = winutils.set_autostart(bool(enabled))
        if not ok:
            self.act_autostart.setChecked(winutils.autostart_enabled())
        self.cfg["autostart"] = winutils.autostart_enabled()

    def show_about(self):
        from PySide6.QtWidgets import QMessageBox
        box = QMessageBox(self)
        box.setWindowTitle(TR("about"))
        box.setTextFormat(Qt.RichText)
        box.setText(TR("about_text"))
        box.setIconPixmap(self._make_icon().pixmap(72, 72))
        box.exec()

    def quit_app(self):
        self._quitting = True
        self._save_state()
        if self.tray is not None:
            self.tray.hide()
        if self.scanner is not None and self.scanner.isRunning():
            self.scanner.stop()
            self.scanner.wait(800)
        self.player.stop()
        QApplication.quit()

    def _save_state(self):
        try:
            self.cfg["geometry"] = base64.b64encode(bytes(self.saveGeometry())).decode("ascii")
            self.cfg["volume"] = self.volume.value() if self.volume.value() == self.player.volume() \
                else self.player.volume()
            self.cfg["shuffle"] = self.player.shuffle()
            self.cfg["repeat"] = self.player.repeat()
            self.cfg.save()
        except Exception:
            pass

    # --------------------------------------------------------------- events
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._adapt_layout()

    def _adapt_layout(self):
        h = self.height()
        w = self.width()
        size = int(max(138, min(272, h * 0.30, w * 0.235)))
        if size != self.cover.width():
            self.cover.setFixedSize(size, size)
            track = self.player.current
            if track is not None:
                self._load_cover_for(track)
        compact = h < 640
        self.lbl_album.setVisible(not compact)
        self.lbl_hint.setVisible(h >= 690)
        self.cover.setVisible(h >= 560)
        self.lbl_now.setVisible(not compact)

    def _tick(self):
        self._spin += 0.6
        self.list.delegate.advance()
        track = self.player.current
        if track is not None and self.player.is_playing:
            self.list.update_row_of(track)

    def _update_status(self, scanning: bool = False):
        if scanning:
            self.lbl_status.setText(f"{TR('scanning')}  {len(self.tracks)}")
            return
        if not self.tracks:
            self.lbl_status.setText("")
            return
        total = sum(t.duration for t in self.tracks if t.duration)
        text = TR("tracks_count", n=len(self.tracks))
        if total:
            text += "   ·   " + TR("total_time", t=_fmt_time(total))
        if len(self.view) != len(self.tracks):
            text += f"   ·   {len(self.view)} / {len(self.tracks)}"
        self.lbl_status.setText(text)

    def status_text(self, text: str, msec: int = 3000):
        self.lbl_status.setText(text)
        QTimer.singleShot(msec, self._update_status)

    def _folder_chip_text(self):
        folder = self.cfg.get("folder")
        if not folder:
            return TR("choose_folder")
        name = os.path.basename(os.path.normpath(folder)) or folder
        fm = QFontMetrics(self.btn_folder.font())
        return fm.elidedText(name, Qt.ElideMiddle, 180)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        paths = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        folders = [p for p in paths if os.path.isdir(p)]
        files = [p for p in paths if os.path.isfile(p) and is_audio(p)]
        if len(folders) == 1 and not files:
            self.load_folder(folders[0])
        elif folders and not files:
            for folder in folders:
                self.tracks.extend(_quick_scan(folder, bool(self.cfg["recursive"])))
            self.tracks = sort_tracks(self.tracks)
            self.refresh_list()
            self.status_text(TR("added_to_queue", n=len(folders)), 3000)
        elif files:
            added = 0
            for path in files:
                self.tracks.append(read_tags(path))
                added += 1
            self.tracks = sort_tracks(self.tracks)
            self.refresh_list()
            self.status_text(TR("added_to_queue", n=added), 3000)
        else:
            self.status_text(TR("dropped_nothing"), 3000)
        event.acceptProposedAction()

    def keyPressEvent(self, event):
        key = event.key()
        if key == Qt.Key_Space:
            self.player.toggle()
        elif key == Qt.Key_Right and event.modifiers() == Qt.NoModifier:
            self._seek_by(5000)
        elif key == Qt.Key_Left and event.modifiers() == Qt.NoModifier:
            self._seek_by(-5000)
        elif key == Qt.Key_Up and event.modifiers() == Qt.NoModifier:
            self.volume.setValue(min(100, self.volume.value() + 4))
        elif key == Qt.Key_Down and event.modifiers() == Qt.NoModifier:
            self.volume.setValue(max(0, self.volume.value() - 4))
        elif key == Qt.Key_Escape:
            if self.search.text():
                self.search.clear()
            else:
                self.hide()
        elif key == Qt.Key_F and event.modifiers() == Qt.ControlModifier:
            self.search.setFocus()
            self.search.selectAll()
        else:
            super().keyPressEvent(event)
            return
        event.accept()

    def closeEvent(self, event):
        self._save_state()
        if (not self._quitting and self.cfg["minimize_to_tray"] and self.tray is not None
                and self.tray.isVisible()):
            event.ignore()
            self.hide()
            self.retranslate()
            if not self.cfg.get("tray_hint_shown"):
                self._maybe_show_tray_hint()
            return
        if self.scanner is not None and self.scanner.isRunning():
            self.scanner.stop()
            self.scanner.wait(800)
        self.player.stop()
        event.accept()


def _fmt_time(seconds: float) -> str:
    secs = int(max(0, seconds))
    h, rem = divmod(secs, 3600)
    m, s = divmod(rem, 60)
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"


def _quick_scan(folder: str, recursive: bool) -> list[Track]:
    found: list[Track] = []
    scan_folder(folder, recursive, batch_size=200, on_batch=lambda b: found.extend(b))
    return found
