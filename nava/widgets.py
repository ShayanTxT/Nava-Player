"""Custom widgets: icon buttons, round cover art with vinyl fallback, seek slider."""
from __future__ import annotations

from PySide6.QtCore import QRectF, QSize, Qt, QTimer, Signal
from PySide6.QtGui import (QColor, QFont, QPainter, QPainterPath, QPen, QPixmap,
                           QRadialGradient)
from PySide6.QtWidgets import QSizePolicy, QSlider, QToolTip, QWidget

from .icons import icon_pixmap
from .theme import Theme


class IconButton(QWidget):
    """Flat, round icon button that follows the current theme colors."""

    clicked = Signal()

    def __init__(self, icon_name: str, size: int = 40, icon_size: int = 20,
                 parent=None, checkable: bool = False, tooltip: str = "",
                 fill: bool = False):
        super().__init__(parent)
        self._icon = icon_name
        self._size = size
        self._icon_size = icon_size
        self._hover = False
        self._checked = False
        self._checkable = checkable
        self._active = False
        self._fill = fill
        self._colors = {"text": "#ffffff", "dim": "#999999", "accent": "#ffffff", "bg": "#000000",
                        "accent2": "#ffffff", "on_accent": "#000000", "panel": "#111111"}
        self.setFixedSize(size, size)
        self.setCursor(Qt.PointingHandCursor)
        self.setAttribute(Qt.WA_Hover, True)
        if tooltip:
            self.setToolTip(tooltip)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

    # --- api -------------------------------------------------------------
    def set_theme(self, theme: Theme):
        self._colors = {
            "text": theme.text, "dim": theme.dim, "accent": theme.accent,
            "bg": theme.bg, "accent2": theme.accent2, "on_accent": theme.on_accent,
            "panel": theme.panel, "border": theme.border,
        }
        self.update()

    def set_icon(self, name: str):
        if name != self._icon:
            self._icon = name
            self.update()

    def set_active(self, active: bool):
        if active != self._active:
            self._active = active
            self.update()

    def is_active(self) -> bool:
        return self._active

    def setChecked(self, value: bool):
        self._checked = bool(value)
        self.update()

    def isChecked(self) -> bool:
        return self._checked

    def set_size(self, size: int, icon_size: int):
        self._size = size
        self._icon_size = icon_size
        self.setFixedSize(size, size)
        self.update()

    def sizeHint(self) -> QSize:
        return QSize(self._size, self._size)

    # --- events ----------------------------------------------------------
    def enterEvent(self, event):
        self._hover = True
        self.update()

    def leaveEvent(self, event):
        self._hover = False
        self.update()

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            event.accept()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton and self.rect().contains(event.position().toPoint()):
            if self._checkable:
                self._checked = not self._checked
            self.clicked.emit()
            self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        r = QRectF(self.rect())
        hovered = self._hover or self._checked or self._active

        if self._fill:
            grad = QRadialGradient(r.center(), r.width() * 0.72)
            grad.setColorAt(0.0, QColor(self._colors["accent"]))
            grad.setColorAt(1.0, QColor(self._colors["accent2"]))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(r.adjusted(1, 1, -1, -1))
            if hovered:
                painter.setBrush(QColor(255, 255, 255, 38))
                painter.drawEllipse(r.adjusted(1, 1, -1, -1))
        elif hovered:
            painter.setBrush(QColor(self._colors.get("border", "#333")))
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(r)

        color = self._colors["text"]
        if self._fill:
            color = self._colors["on_accent"]
        elif self._active or self._checked:
            color = self._colors["accent"]
        elif hovered:
            color = self._colors["text"]
        else:
            color = self._colors["dim"]

        dpr = self.devicePixelRatioF()
        pm = icon_pixmap(self._icon, color, self._icon_size, 1.9, dpr)
        w = pm.width() / pm.devicePixelRatio()
        h = pm.height() / pm.devicePixelRatio()
        painter.drawPixmap(int((r.width() - w) / 2), int((r.height() - h) / 2), pm)
        painter.end()


class CoverWidget(QWidget):
    """Rounded cover art (or a cozy spinning vinyl if the file has no artwork)."""

    def __init__(self, size: int = 240, parent=None):
        super().__init__(parent)
        self._size = size
        self.setFixedSize(size, size)
        self._pix: QPixmap | None = None
        self._angle = 0.0
        self._playing = False
        self._colors = {"accent": "#e8a87c", "accent2": "#d2803f", "panel": "#231a15",
                        "border": "#3b2d24", "dim": "#a8917f", "panel2": "#2c211a",
                        "bg": "#171210", "text": "#fff"}
        self._timer = QTimer(self)
        self._timer.setInterval(40)
        self._timer.timeout.connect(self._tick)

    def set_theme(self, theme: Theme):
        self._colors = {"accent": theme.accent, "accent2": theme.accent2, "panel": theme.panel,
                        "border": theme.border, "dim": theme.dim, "panel2": theme.panel2,
                        "bg": theme.bg, "text": theme.text}
        self.update()

    def set_image(self, image):
        if image is None or image.isNull():
            self._pix = None
            self.update()
            return
        dpr = self.devicePixelRatioF()
        pix = QPixmap.fromImage(image).scaled(int(self._size * dpr), int(self._size * dpr),
                                              Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation)
        pix.setDevicePixelRatio(dpr)
        self._pix = pix
        self.update()

    def set_playing(self, playing: bool):
        self._playing = playing
        if playing and self._pix is None:
            self._timer.start()
        else:
            self._timer.stop()
        self.update()

    def _tick(self):
        self._angle = (self._angle + 1.1) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing, True)
        side = min(self.width(), self.height())
        rect = QRectF((self.width() - side) / 2, (self.height() - side) / 2, side, side)

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(0, 0, 0, 90))
        painter.drawEllipse(rect.adjusted(2, 5, -2, -2))

        if self._pix is not None:
            path = QPainterPath()
            path.addEllipse(rect)
            painter.setClipPath(path)
            painter.drawPixmap(rect.toRect(), self._pix)
            painter.setClipping(False)
            pen = QPen(QColor(self._colors["border"]), 2)
            painter.setPen(pen)
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect.adjusted(1, 1, -1, -1))
        else:
            # cozy vinyl record
            grad = QRadialGradient(rect.center(), side / 2)
            grad.setColorAt(0.0, QColor(self._colors["panel2"]))
            grad.setColorAt(0.62, QColor(self._colors["panel"]))
            grad.setColorAt(1.0, QColor(self._colors["bg"]))
            painter.setBrush(grad)
            painter.setPen(Qt.NoPen)
            painter.drawEllipse(rect)

            painter.save()
            painter.translate(rect.center())
            painter.rotate(self._angle)
            ring_pen = QPen(QColor(255, 255, 255, 16), 1)
            painter.setPen(ring_pen)
            painter.setBrush(Qt.NoBrush)
            for i in range(6):
                rr = side * (0.20 + 0.055 * i)
                painter.drawEllipse(QRectF(-rr, -rr, rr * 2, rr * 2))
            painter.setPen(Qt.NoPen)
            painter.setBrush(QColor(self._colors["accent"]))
            painter.drawEllipse(QRectF(-side * 0.045, -side * 0.045, side * 0.09, side * 0.09))
            painter.setBrush(QColor(self._colors["panel"]))
            painter.drawEllipse(QRectF(-side * 0.016, -side * 0.016, side * 0.032, side * 0.032))
            painter.restore()

            painter.setPen(QPen(QColor(self._colors["border"]), 2))
            painter.setBrush(Qt.NoBrush)
            painter.drawEllipse(rect.adjusted(1, 1, -1, -1))

            if self._playing:
                font = QFont(self.font())
                font.setPointSizeF(max(7.5, side * 0.045))
                painter.setFont(font)
                painter.setPen(QColor(self._colors["dim"]))
                text = "♪ ♫ ♪"
                painter.drawText(rect.adjusted(0, side * 0.62, 0, 0), Qt.AlignHCenter | Qt.AlignTop, text)
        painter.end()


class SeekSlider(QSlider):
    # (click-to-seek + hover time preview)
    """Horizontal slider that jumps where you click and previews the time on hover."""

    seek_requested = Signal(int)   # 0..1000

    def __init__(self, parent=None):
        super().__init__(Qt.Horizontal, parent)
        self.setRange(0, 1000)
        self.setObjectName("SeekSlider")
        self.setCursor(Qt.PointingHandCursor)
        self._duration = 0.0
        self._preview_enabled = True

    def set_duration(self, seconds: float):
        self._duration = max(0.0, seconds or 0.0)

    def _value_from_x(self, x: float) -> int:
        span = max(1, self.width())
        return int(max(0.0, min(1.0, x / span)) * 1000)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            value = self._value_from_x(event.position().x())
            self.setValue(value)
            self.seek_requested.emit(value)
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._preview_enabled and self._duration > 0:
            value = self._value_from_x(event.position().x())
            secs = self._duration * value / 1000.0
            m, s = divmod(int(secs), 60)
            h, m = divmod(m, 60)
            text = f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
            QToolTip.showText(event.globalPosition().toPoint(), text, self)
        super().mouseMoveEvent(event)

    def wheelEvent(self, event):
        # volume-style scroll on the seek bar is more annoying than useful
        event.ignore()
