#!/usr/bin/env python3
"""Nava Player — a cozy offline music player.

Usage:
    python main.py                # start the player
    python main.py "D:/Music"     # start and load a folder

Run at login:  python main.py --autostart     (starts hidden in the tray)
Troubleshooting:
    python main.py --diagnose                 # print an audio/backend report
    python main.py --smoketest "D:/Music"     # play 3s of the first track, then exit
"""
from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def main() -> int:
    # make multi-monitor / HiDPI screens look right
    try:
        from PySide6.QtCore import Qt
        from PySide6.QtGui import QGuiApplication
        QGuiApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough)
    except Exception:
        pass

    from PySide6.QtCore import Qt
    from PySide6.QtGui import QIcon
    from PySide6.QtWidgets import QApplication

    QApplication.setApplicationName("Nava Player")
    QApplication.setOrganizationName("Nava")
    QApplication.setApplicationDisplayName("Nava Player")

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)      # keep playing in the background

    # proper taskbar grouping + icon on Windows
    if sys.platform.startswith("win"):
        try:
            import ctypes
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Nava.MusicPlayer.1")
        except Exception:
            pass

    from nava import winutils
    from nava.config import Config
    from nava.window import MainWindow

    if "--diagnose" in sys.argv:
        return diagnose()

    cfg = Config()

    folder_arg = None
    show_window = True
    for arg in sys.argv[1:]:
        if arg == "--autostart":
            show_window = bool(cfg.get("start_visible", False))
        elif arg in ("--minimized", "--tray"):
            show_window = False
        elif not arg.startswith("-") and os.path.isdir(arg):
            folder_arg = arg
        elif not arg.startswith("-") and arg:
            folder_arg = arg

    if folder_arg and os.path.isdir(folder_arg):
        cfg["folder"] = folder_arg

    window = MainWindow(cfg)
    icon = window._make_icon()
    ico_path = _resource("nava.ico")
    if os.path.isfile(ico_path):
        file_icon = QIcon(ico_path)
        if not file_icon.isNull():
            icon = file_icon
    app.setWindowIcon(icon)
    window.setWindowIcon(icon)

    if "--smoketest" in sys.argv:
        return smoketest(app, window)

    if show_window:
        window.show()
        winutils.apply_windows_extras(window)

    return app.exec()


def _resource(*parts: str) -> str:
    from nava.config import resource_path
    return resource_path(*parts)


def diagnose() -> int:
    """Print a short report about the audio stack — helpful when a PC has no sound."""
    from PySide6 import QtCore
    from PySide6.QtMultimedia import QMediaDevices

    print("Nava Player — diagnostics")
    print("  Qt:", QtCore.qVersion(), "| PySide6:", QtCore.__version__ if hasattr(QtCore, "__version__") else "-")
    print("  frozen:", bool(getattr(sys, "frozen", False)), "| exe:", sys.executable)
    try:
        outs = QMediaDevices.audioOutputs()
        print("  audio outputs:", len(outs))
        for dev in outs:
            print("    -", dev.description(), "| default:", dev.isDefault())
        if not outs:
            print("    (no output device found — check Windows sound settings)")
    except Exception as exc:
        print("  audio outputs: error ->", exc)

    from PySide6.QtCore import QTimer, QUrl
    from PySide6.QtMultimedia import QAudioOutput, QMediaPlayer
    from PySide6.QtWidgets import QApplication

    sample = _resource("assets", "diag-tone.wav")
    if not os.path.isfile(sample):
        print("  decode test skipped: sample file missing")
        return 0
    try:
        player = QMediaPlayer()
        player.setAudioOutput(QAudioOutput())
        player.setSource(QUrl.fromLocalFile(sample))
        player.play()

        def report():
            ok = player.duration() > 0
            print(f"  audio backend decodes the test tone: {ok} "
                  f"(duration {player.duration()} ms, position {player.position()} ms)")
            if not ok:
                print("  -> if playback fails on this PC, install "
                      "'Microsoft Visual C++ Redistributable' and check the sound device")
            app = QApplication.instance()
            if app is not None:
                app.quit()

        QTimer.singleShot(1600, report)
        return QApplication.instance().exec()
    except Exception as exc:
        print("  decode test failed:", exc)
    return 0


def smoketest(app, window) -> int:
    """Headless-ish end-to-end check used by the build pipeline."""
    from PySide6.QtCore import QTimer

    window.show()
    result = {"ok": False}

    def check():
        tracks = window.tracks
        print("[smoketest] scanned tracks:", len(tracks), flush=True)
        if not tracks:
            print("[smoketest] FAIL: no tracks found", flush=True)
            app.quit()
            return
        window.play_library_index(0)
        print("[smoketest] playing:", window.player.current.display_title, flush=True)

    def verify():
        pc = window.player
        pos = pc.position()
        print(f"[smoketest] playing={pc.is_playing} pos={pos}ms dur={pc.duration()}ms "
              f"volume={pc.volume()}", flush=True)
        if pos > 300:
            print("[smoketest] OK", flush=True)
            result["ok"] = True
        else:
            print("[smoketest] FAIL: no progress", flush=True)
        pc.next()
        QTimer.singleShot(1200, after_next)

    def after_next():
        print("[smoketest] after next:", window.player.current.display_title,
              "| playing:", window.player.is_playing, flush=True)
        print("[smoketest] tray available:", window.tray is not None, flush=True)
        window.close()                      # must hide, not quit, and keep playing
        QTimer.singleShot(800, after_close)

    def after_close():
        hidden = not window.isVisible()
        still_playing = window.player.is_playing
        print(f"[smoketest] background mode: window hidden={hidden} "
              f"still playing={still_playing}", flush=True)
        if not (hidden and still_playing):
            result["ok"] = False
        out_dir = os.path.dirname(sys.executable) if getattr(sys, "frozen", False) else os.getcwd()
        img = window.grab().save(os.path.join(out_dir, "smoketest-window.png"))
        print("[smoketest] screenshot saved:", img, flush=True)
        print("[smoketest] RESULT:", "OK" if result["ok"] else "FAILED", flush=True)
        window.quit_app()
        app.exit(0 if result["ok"] else 1)

    QTimer.singleShot(6000, check)
    QTimer.singleShot(11000, verify)
    QTimer.singleShot(30000, app.quit)
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
