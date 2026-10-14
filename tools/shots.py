"""Generate the screenshot set used by the README files.

    python tools/shots.py [output_dir]

Works both natively (Linux/macOS) and inside Wine on Windows.
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtCore import QTimer                      # noqa: E402
from PySide6.QtGui import QImage                       # noqa: E402
from PySide6.QtWidgets import QApplication             # noqa: E402

from nava.config import Config                         # noqa: E402
from nava.library import extract_cover                 # noqa: E402
from nava.theme import THEME_BY_KEY                    # noqa: E402
from nava.window import MainWindow                     # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "screenshots")
MUSIC = os.path.join(os.path.dirname(ROOT), "test-music")
os.makedirs(OUT, exist_ok=True)

app = QApplication(sys.argv)
cfg = Config(path=os.path.join(ROOT, "tools", "_shot_config.json"))
cfg["folder"] = MUSIC
cfg["lang"] = "en"
cfg["theme"] = "coffee"

win = MainWindow(cfg)
win.resize(1180, 762)
win.show()


def shot(name):
    ok = win.grab().save(os.path.join(OUT, name))
    print(f"[shot] {name} :: {ok}", flush=True)


def playing_state(index=1):
    win.play_library_index(index)
    track = win.tracks[index]
    win._on_track_changed(track)
    data = extract_cover(track.path)
    if data:
        img = QImage()
        img.loadFromData(data)
        win.cover.set_image(img)
    win.cover.set_playing(True)
    win.btn_play.set_icon("pause")
    win.seek.set_duration(track.duration or 245)
    win.seek.setValue(360)
    win.lbl_pos.setText("2:32")
    win.lbl_dur.setText(track.duration_text)
    win.list.setCurrentRow(min(index, win.list.count() - 1))


def s0():
    if not win.tracks:
        print("[shot] no tracks found - is the test music folder there?", flush=True)
        app.quit()
        return
    playing_state(1)
    QTimer.singleShot(900, lambda: shot("01-playing-en.png"))
    QTimer.singleShot(1500, s1)


def s1():
    win.apply_theme(THEME_BY_KEY["forest"])
    win._on_track_changed(win.player.current)
    QTimer.singleShot(800, lambda: shot("02-theme-forest-en.png"))
    QTimer.singleShot(1500, s2)


def s2():
    win.apply_theme(THEME_BY_KEY["coffee"])
    QTimer.singleShot(600, s3)


def s3():
    # the menu is a popup of its own: grab it directly, plus the window behind it
    from nava.icons import app_icon_pixmap
    win.menu.popup(win.mapToGlobal(win.rect().topLeft()))
    QTimer.singleShot(600, s4)


def s4():
    ok = win.menu.grab().save(os.path.join(OUT, "03-menu-en.png"))
    print("[shot] 03-menu-en.png ::", ok, flush=True)
    win.menu.close()
    QTimer.singleShot(400, s5)


def s5():
    from nava.icons import app_icon_pixmap
    app_icon_pixmap(256, "#e8a87c", "#d2803f", "#22160e").save(os.path.join(OUT, "00-icon.png"))
    win.set_lang("fa")
    win.apply_theme(THEME_BY_KEY["coffee"])
    QTimer.singleShot(900, lambda: shot("04-persian-ui.png"))
    QTimer.singleShot(1600, s6)


def s6():
    win.set_lang("en")
    win.tracks = []
    win.player.stop()
    win.player.set_queue([], autoplay=False)   # proper API (never poke .queue directly)
    win.refresh_list()
    QTimer.singleShot(800, lambda: shot("05-empty-state-en.png"))
    QTimer.singleShot(1500, s7)


def s7():
    win.resize(940, 620)
    QTimer.singleShot(900, lambda: shot("06-compact-en.png"))
    QTimer.singleShot(1500, done)


def done():
    print("[shot] all screenshots written to", OUT, flush=True)
    app.quit()


QTimer.singleShot(3800, s0)
QTimer.singleShot(40000, app.quit)
sys.exit(app.exec())
