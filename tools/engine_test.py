"""Functional check of PlayerController: play/next/prev/volume/seek/repeat/shuffle."""
import os, sys
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication
from nava.library import read_tags, sort_tracks
from nava.player import PlayerController

MUSIC = os.path.join(os.path.dirname(ROOT), "test-music")
app = QApplication(sys.argv)
pc = PlayerController()
log = []
pc.error.connect(lambda m: log.append(("ERROR", m)))
pc.track_changed.connect(lambda t: log.append(("TRACK", t.display_title if t else None)))
pc.playing_changed.connect(lambda p: log.append(("PLAYING", p)))
pc.position_changed.connect(lambda ms: None)

tracks = []
for root, _dirs, files in os.walk(MUSIC):
    for f in sorted(files):
        if f.lower().endswith((".mp3", ".wav")):
            tracks.append(read_tags(os.path.join(root, f)))
tracks = sort_tracks(tracks)
print("library:", len(tracks), "tracks", flush=True)

steps = []
def step(fn):
    steps.append(fn)

shots = {}

def s1():
    pc.set_queue(tracks, 0, autoplay=True)
    print("[1] play first ->", pc.current.display_title if pc.current else None, flush=True)

def s2():
    print("[2] state:", "playing" if pc.is_playing else "not playing",
          "| pos:", pc.position(), "ms | dur:", pc.duration(), "ms", flush=True)

def s3():
    print("[3] volume before:", pc.volume(), flush=True)
    pc.set_volume(35)
    print("[3] volume after set 35:", pc.volume(), flush=True)
    pc.set_muted(True)
    print("[3] muted:", pc.is_muted(), flush=True)
    pc.set_muted(False)

def s4():
    pc.next()
    print("[4] next ->", pc.current.display_title if pc.current else None, flush=True)

def s5():
    pc.prev()
    print("[5] prev ->", pc.current.display_title if pc.current else None, flush=True)

def s6():
    pc.set_position(5000)
    print("[6] seek to 5s -> pos:", pc.position(), flush=True)

def s7():
    pc.set_shuffle(True)
    print("[7] shuffle:", pc.shuffle(), "| current kept:",
          pc.current.display_title if pc.current else None, flush=True)
    pc.set_shuffle(False)

def s8():
    print("[8] repeat cycle:", pc.cycle_repeat(), pc.cycle_repeat(), pc.cycle_repeat(), flush=True)
    pc.pause()
    print("[8] paused, playing =", pc.is_playing, flush=True)

def s9():
    pc.play()
    print("[9] resumed, playing =", pc.is_playing, flush=True)
    print("=== events:", log[:14], flush=True)
    print("=== done", flush=True)
    app.quit()

for i, fn in enumerate([s1, s2, s3, s4, s5, s6, s7, s8, s9]):
    QTimer.singleShot(700 + i * 900, fn)
QTimer.singleShot(20000, app.quit)
sys.exit(app.exec())
