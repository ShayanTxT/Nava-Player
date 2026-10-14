# 🛠 Build Nava.exe on Windows

A complete walkthrough: install Python → test → build `Nava.exe`.
Takes about **5 minutes** (plus ~120 MB of package downloads).

🇮🇷 نسخه‌ی فارسی: **[HOWTO-build-exe.fa.md](HOWTO-build-exe.fa.md)**

---

## 0) Requirements (once)

| | |
|---|---|
| OS | Windows 10 or 11, 64-bit |
| Python | **3.10+ (64-bit)** — [python.org/downloads](https://www.python.org/downloads/) |
| Internet | Only to install the packages; the player itself is fully offline |

### Installing Python (the important part)

1. Download **Windows installer (64-bit)** from [python.org/downloads](https://www.python.org/downloads/) (e.g. Python 3.11.x).
2. On the first installer screen, tick **“Add python.exe to PATH”** ✅ — without it the commands below won’t work.
3. Click **Install Now** and wait.
4. Verify: press `Win + R`, type `cmd`, hit Enter, then run:

```bat
python --version
```

`Python 3.11.x` means you’re ready. If it says “not recognized”, try `py -3 --version`
and use `py -3` instead of `python` everywhere below.

---

## 1) The easy way: double-click 🖱

1. Extract the project somewhere simple, e.g.:

```
C:\nava-player\
```

> ⚠️ Avoid non-English characters or fancy symbols in the path (e.g. `C:\My Stuff\Player`).
> `C:\nava-player` is a safe choice.

2. Double-click **`build.bat`**.
3. A console window runs three steps:

```
[1/3] Checking Python...           → installs PySide6, mutagen, pyinstaller
[2/3] Preparing the icon...        → generates nava.ico
[3/3] Building dist\Nava.exe ...   → creates the executable (1–3 minutes)
```

4. When it prints **`Done!`**, your executable is here:

```
C:\nava-player\dist\Nava.exe
```

That’s it 🎉 `Nava.exe` is a single file — copy it to your desktop or anywhere else.

---

## 2) The manual way: four commands

Open the project folder in File Explorer, type `cmd` in the address bar and hit Enter
(or shift-right-click → *Open in Terminal*), then:

```bat
REM 1 – dependencies (first time only, ~100 MB)
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller

REM 2 – app icon (only needed if you changed the icon)
python tools\make_ico.py

REM 3 – build
python -m PyInstaller --noconfirm --clean Nava.spec

REM 4 – the result
dir dist
```

Output: **`dist\Nava.exe`** (around 50 MB — that’s normal; Qt’s runtime and the audio codecs are bundled inside).

---

## 3) Test before building (recommended)

```bat
python main.py
```

If the Nava window opens and plays a track, the exe will work too.

---

## 4) Running the exe & the SmartScreen note

- Double-click `Nava.exe`. The very first launch takes a few seconds longer (the single-file bundle unpacks), later launches are fast.
- Because the file has **no digital signature (code signing)**, Windows may show the blue
  *“Windows protected your PC”* dialog → **More info → Run anyway**.
- To silence that warning on your own machine (optional, PowerShell):

```powershell
Unblock-File .\dist\Nava.exe
```

> If you share the exe, others will see the same prompt. Removing it entirely requires a
> code-signing certificate (~$200/year) and `signtool` — not needed for personal use.

**Verify audio works on any machine:**

```bat
dist\Nava.exe --diagnose
```

It reports how many audio output devices Windows exposes and runs a decode test.

---

## 5) Customising the build

| Goal | How |
|---|---|
| Rename the output | change `name="Nava"` in `Nava.spec` |
| Change the icon | replace `nava.ico` (256×256) and run `build.bat` again |
| See errors in a console | set `console=True` in `Nava.spec` |
| Smaller / faster start | build the *onedir* variant (below) |
| Fewer antivirus false positives | *onedir* is usually friendlier |

### onedir mode (a folder + exe, starts faster)

Instead of one 50 MB file you get a folder containing `Nava.exe` next to Qt’s libraries
(move the whole folder around):

```bat
python -m PyInstaller --noconfirm --clean --onedir --windowed ^
  --name Nava --icon nava.ico --add-data "nava.ico;." ^
  --hidden-import mutagen.mp3 --hidden-import mutagen.mp4 --hidden-import mutagen.flac ^
  --hidden-import mutagen.oggvorbis --hidden-import mutagen.oggopus --hidden-import mutagen.wave ^
  --hidden-import mutagen.aiff --hidden-import mutagen.asf ^
  --exclude-module PySide6.QtQml --exclude-module PySide6.QtQuick ^
  --exclude-module PySide6.QtWebEngineCore --exclude-module PySide6.Qt3DCore ^
  --exclude-module tkinter --exclude-module unittest ^
  main.py
```

Output: `dist\Nava\Nava.exe`

### GUI alternative (for beginners)

```bat
python -m pip install auto-py-to-exe
auto-py-to-exe
```

Script = `main.py`, mode = **Onefile**, **Window Based (hide the console)**, pick `nava.ico`, click **Convert**.

### Or let GitHub build it

Push the repo to GitHub and run the **Build Windows EXE** workflow
(*Actions → Build Windows EXE → Run workflow*). The finished `Nava.exe` is attached to the run as an artifact —
handy if you don’t have a Windows machine at hand.

---

## 6) Common errors & fixes

| Message / problem | Fix |
|---|---|
| `'python' is not recognized...` | Reinstall Python with “Add python.exe to PATH”, or use `py -3`. Close and reopen the terminal |
| `pip` hangs / SSL errors | `python -m pip install --upgrade pip`, then retry (check VPN/proxy) |
| `ModuleNotFoundError: PySide6` while building | `python -m pip install PySide6 mutagen pyinstaller` |
| exe builds but doesn’t open | set `console=True` in `Nava.spec`, rebuild, launch from a terminal to read the traceback |
| “Failed to execute script” | same as above; usually a missing module → add `--hidden-import <module>` |
| Antivirus quarantines the exe | PyInstaller false positive: add an exception, or build the *onedir* variant |
| `Access is denied` while building | move the project somewhere writable (not `C:\Program Files`) and delete old `build`/`dist` |
| Build seems stuck | first build is slow (PySide6 is big); later builds are much faster |
| `RecursionError` | `python -m pip install --upgrade pyinstaller`, then `--noconfirm --clean` |

---

## 7) What the build creates

```
C:\nava-player\
├── build\        ← temporary files (safe to delete)
├── dist\
│   └── Nava.exe  ← 🎯 your executable
├── main.py
├── Nava.spec     ← build recipe (name, icon, console/windowed)
├── nava\         ← application code
└── tools\
```

After changing the code, just run `build.bat` again to produce a fresh exe.
For quick tests you don’t need an exe at all — `python main.py` runs the current code immediately.

---

## 8) 30-second checklist

- [ ] 64-bit Python installed, `python --version` answers
- [ ] Project extracted to a plain path (`C:\nava-player`)
- [ ] `python main.py` opens the player
- [ ] `build.bat` finished with `Done!`
- [ ] `dist\Nava.exe` opens when double-clicked
- [ ] Inside the exe: “Choose folder” loads your music
