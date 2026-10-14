# 🎧 Nava — a cozy offline music player

**Nava** is a lightweight, good-looking **offline music player for Windows** that keeps playing in the background.
Point it at a folder of music, and it reads your tracks, tags and cover art — no account, no internet, no nonsense.

[فارسی: راهنمای کامل فارسی](README.fa.md) · [Build your own .exe](HOWTO-build-exe.md) · [راهنمای ساخت exe](HOWTO-build-exe.fa.md)

![platform](https://img.shields.io/badge/platform-Windows%2010%2F11-0078D6?logo=windows)
![python](https://img.shields.io/badge/python-3.10%2B-3776AB?logo=python&logoColor=white)
![Qt](https://img.shields.io/badge/Qt-6-41CD52?logo=qt&logoColor=white)
![license](https://img.shields.io/badge/license-MIT-yellow)

![Nava Player](screenshots/01-playing-en.png)

---

## ✨ Features

| | |
|---|---|
| 📁 **Folder-based library** | Give it a folder (or drop one on the window) and it scans every audio file, optionally including subfolders |
| 🎵 **Many formats** | mp3, m4a/aac, flac, wav, ogg/opus, wma, aiff, ape, wv |
| 🖼 **Cover art** | Embedded artwork (ID3 / FLAC / MP4 / WMA) or a `cover.jpg` sitting next to the tracks |
| 🏷 **Tags & durations** | Title, artist, album, track number and length read with [mutagen](https://mutagen.readthedocs.io/) |
| 🌙 **Runs in the background** | Closing the window hides it to the system tray — playback keeps going |
| 🖱 **Tray menu** | Play/pause, next, previous, show/hide window, quit |
| 🎨 **4 cozy themes** | Coffee & Caramel, Midnight Forest, Indigo Night, Warm Sunset |
| 🌐 **English & Persian** | English by default; switch from *Menu → Language → فارسی* (full RTL layout) |
| 🔎 **Search** | Instant filtering on title / artist / album |
| 🔀 **Shuffle & repeat** | Repeat one · repeat all · shuffle |
| ⌨️ **Keyboard & media keys** | Space, ← →, ↑ ↓, plus the hardware media keys on your keyboard/headset |
| 🚀 **Run at Windows startup** | One toggle in the menu (starts quietly in the tray) |
| 📌 **Always on top** | Keep Nava pinned over other windows |
| 🖥 **HiDPI friendly** | Sharp on scaled and multi-monitor setups |

---

## 📸 Screenshots

| Now playing (Coffee & Caramel) | Midnight Forest theme |
|---|---|
| ![](screenshots/01-playing-en.png) | ![](screenshots/02-theme-forest-en.png) |

| The menu | Persian interface (RTL) |
|---|---|
| ![](screenshots/03-menu-en.png) | ![](screenshots/04-persian-ui.png) |

| Empty state | Compact window |
|---|---|
| ![](screenshots/05-empty-state-en.png) | ![](screenshots/06-compact-en.png) |

![icon](screenshots/00-icon.png)

---

## ⬇️ Get Nava (Windows)

**Option A — build the exe yourself (2 clicks, ~5 minutes)**

1. Download this repository (**Code → Download ZIP**) and extract it to a simple path like `C:\nava-player`.
2. Install [Python 3.11 (64-bit)](https://www.python.org/downloads/) — tick **“Add python.exe to PATH”** in the installer.
3. Double-click **`build.bat`** → your executable appears at **`dist\Nava.exe`**.

Full walkthrough with troubleshooting: **[HOWTO-build-exe.md](HOWTO-build-exe.md)**

**Option B — let GitHub build it for you**

Fork/push this repo to GitHub and run the **Build Windows EXE** workflow
(*Actions → Build Windows EXE → Run workflow*). Download `Nava.exe` from the run’s
**Artifacts** section — no Windows PC needed.

> 🔐 **About SmartScreen:** `Nava.exe` is not code-signed, so the first launch may show
> *“Windows protected your PC”* → click **More info → Run anyway**.
> You can also run `Unblock-File .\Nava.exe` in PowerShell.

### First run

1. Click **“Choose folder”** and pick the folder that holds your music.
2. Play anything from the list; cover art, tags and durations show up automatically.
3. Close the window whenever you like — Nava stays in the tray and keeps playing.
   Right-click the tray icon (next to the clock) to quit for real. `Ctrl+Q` also quits.

---

## 🛠 Run from source

Requires **Python 3.10+** (tested on 3.11) — works on Windows, Linux and macOS.

```bash
git clone https://github.com/<your-username>/nava-player.git
cd nava-player
pip install -r requirements.txt
python main.py
```

Start straight into a folder:

```bash
python main.py "D:/Music"
```

Handy switches:

```bash
python main.py --diagnose              # report audio devices + decode test
python main.py --smoketest "D:/Music"  # scan, play 3 s, verify background mode, exit
python main.py --autostart             # how it starts when Windows boots it
```

---

## 📦 Build the Windows executable

The short version (inside the project folder on Windows):

```bat
python -m pip install -r requirements.txt pyinstaller
python tools\make_ico.py
python -m PyInstaller --noconfirm --clean Nava.spec
```

→ `dist\Nava.exe` (single file, windowed, ~50 MB — Qt and the audio codecs are inside).

Prefer clicking? Just run **`build.bat`**.
Details, onedir mode, icon/name changes and every common error: **[HOWTO-build-exe.md](HOWTO-build-exe.md)**.

---

## ⌨️ Keyboard shortcuts

| Key | Action |
|---|---|
| `Space` | Play / pause |
| `←` / `→` | Seek 5 seconds |
| `↑` / `↓` | Volume up / down |
| `Ctrl+O` | Choose folder |
| `Ctrl+F` | Focus search |
| `Ctrl+S` | Toggle shuffle |
| `Ctrl+R` | Cycle repeat mode |
| `Ctrl+Q` | Quit completely |
| `Esc` | Hide the window (music keeps playing) |
| Media keys | Play/pause, next, previous |

---

## ☰ Menu (the list icon in the header)

- Choose folder · Change folder · Show in folder · Include subfolders
- Theme → 4 palettes
- Language → English / فارسی
- Always on top
- **Close = keep running in background** (turn it off if you want X to really quit)
- Run at Windows startup
- About Nava · Quit

---

## 📂 Project layout

```
nava-player/
├── main.py                 # entry point (+ --diagnose / --smoketest / --autostart)
├── Nava.spec               # PyInstaller build recipe
├── build.bat               # one-click Windows build
├── requirements.txt
├── nava.ico                # multi-size app icon
├── assets/                 # test tone used by --diagnose
├── screenshots/
├── nava/
│   ├── window.py           # main window, track list, tray, menus
│   ├── player.py           # playback engine (QMediaPlayer): queue, shuffle, repeat
│   ├── library.py          # folder scanning, tags and cover art via mutagen
│   ├── widgets.py          # icon buttons, round cover widget, seek slider
│   ├── theme.py            # palettes + global stylesheet
│   ├── icons.py            # inline SVG icons + app icon
│   ├── i18n.py             # English / Persian strings
│   ├── config.py           # settings in %APPDATA%\NavaPlayer\config.json
│   └── winutils.py         # autostart, dark title bar, taskbar thumbnail buttons
└── tools/                  # make_ico.py, shots.py, engine_test.py
```

**Settings** live in `%APPDATA%\NavaPlayer\config.json` (last folder, volume, theme, language, window geometry…).

---

## 🔧 Troubleshooting

**No sound?** Run the built-in check on the machine:

```bat
Nava.exe --diagnose
```

It lists the audio output devices Windows reports and runs a decode test on a bundled tone.
Also make sure the [Microsoft Visual C++ Redistributable (x64)](https://aka.ms/vs/17/release/vc_redist.x64.exe) is installed — it is on virtually every Windows PC already.

**The exe won’t start / DLL error?** Install the VC++ redistributable above, then rebuild with `build.bat`.

**A flac/wma file won’t play?** Playback uses Qt’s bundled FFmpeg backends; mp3/m4a/wav always work.

**Huge folder feels slow?** Scanning runs on a worker thread and streams results, so the UI never freezes.
For very large collections turn off *Include subfolders*.

**Antivirus flags the exe?** Unsigned PyInstaller executables sometimes get false positives —
add the folder to your antivirus exceptions, or build the slightly-lighter *onedir* variant (see the HOWTO).

---

## 🤝 Contributing

Issues and pull requests are welcome. Handy tips:

- Keep the UI strings in `nava/i18n.py` (both languages) and theme colors in `nava/theme.py`.
- `python tools/shots.py` regenerates the screenshots in this README.
- `python tools/engine_test.py` exercises play/next/prev/seek/shuffle/repeat without a GUI.

## 📜 License

MIT — see [LICENSE](LICENSE). Free to use, modify and share.

Built with [Qt for Python (PySide6)](https://doc.qt.io/qtforpython/) and [mutagen](https://mutagen.readthedocs.io/).
Icons are drawn from inline SVG, so the app ships without a single external asset.
