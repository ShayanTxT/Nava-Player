# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for Nava Player — builds a single-file Windows executable.

    pyinstaller --noconfirm --clean Nava.spec
"""

import sys

BLOCK_CIPHER = None

# Modules we never use — dropping them keeps the exe lean.
EXCLUDES = [
    "tkinter", "unittest", "pydoc", "doctest", "pdb",
    "PySide6.QtQml", "PySide6.QtQuick", "PySide6.QtQuickWidgets",
    "PySide6.QtQuickControls2", "PySide6.QtWebEngineCore", "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebChannel", "PySide6.QtWebSockets", "PySide6.QtWebView",
    "PySide6.Qt3DCore", "PySide6.Qt3DRender", "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras", "PySide6.Qt3DInput", "PySide6.Qt3DLogic",
    "PySide6.QtCharts", "PySide6.QtDataVisualization", "PySide6.QtGraphs",
    "PySide6.QtDesigner", "PySide6.QtUiTools", "PySide6.QtHelp", "PySide6.QtSql",
    "PySide6.QtTest", "PySide6.QtPdf", "PySide6.QtPdfWidgets", "PySide6.QtBluetooth",
    "PySide6.QtNfc", "PySide6.QtPositioning", "PySide6.QtSensors",
    "PySide6.QtSerialPort", "PySide6.QtRemoteObjects", "PySide6.QtScxml",
    "PySide6.QtStateMachine", "PySide6.QtSpatialAudio", "PySide6.QtTextToSpeech",
    "PySide6.QtHttpServer", "PySide6.QtNetworkAuth", "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets", "PySide6.QtConcurrent", "PySide6.QtLocation",
    "PySide6.QtSerialBus", "PySide6.QtSvgWidgets",
]

# mutagen resolves tag parsers lazily — make sure they all travel with the exe.
HIDDEN = [
    "mutagen.mp3", "mutagen.mp4", "mutagen.flac", "mutagen.oggvorbis",
    "mutagen.oggopus", "mutagen.oggtheora", "mutagen.wave", "mutagen.aiff",
    "mutagen.asf", "mutagen.apev2", "mutagen.musepack", "mutagen.monkeysaudio",
    "mutagen.id3", "mutagen.easyid3", "mutagen._vorbis", "mutagen._util",
    "nava", "nava.window", "nava.player", "nava.library", "nava.theme",
    "nava.widgets", "nava.icons", "nava.i18n", "nava.config", "nava.winutils",
]

a = Analysis(
    ["main.py"],
    pathex=[],
    binaries=[],
    datas=[("nava.ico", "."), ("assets/diag-tone.wav", "assets")],
    hiddenimports=HIDDEN,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=EXCLUDES,
    noarchive=False,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="Nava",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    runtime_tmpdir=None,
    console=False,          # windowed app (no black console window)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="nava.ico",
    version="tools/version_info.txt",
)
