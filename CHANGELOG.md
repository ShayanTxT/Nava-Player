# Changelog

All notable changes to Nava Player are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/); versions follow [SemVer](https://semver.org/).

## [1.0.0] — 2026-10-14

First public release. 🎉

### Added
- Folder-based music library: pick a folder (or drag & drop it) and Nava scans every audio file,
  optionally including subfolders. Scanning runs on a worker thread and streams results, so the UI never freezes.
- Metadata, duration and album art via [mutagen](https://mutagen.readthedocs.io/):
  embedded artwork (ID3 / FLAC / MP4 / WMA / Vorbis) and `cover.jpg` / `folder.jpg` fallbacks.
- Playback engine on QtMultimedia: play/pause, next/previous, click-to-seek bar with hover time preview,
  volume + mute, shuffle, and repeat off / all / one.
- **Background playback**: closing the window hides it to the system tray; the tray menu has
  play/pause, next, previous, show/hide and quit. `Ctrl+Q` still quits for real.
- Cozy, modern UI with four themes: Coffee & Caramel, Midnight Forest, Indigo Night, Warm Sunset.
- Bilingual interface — **English (default)** and **Persian** with a full right-to-left layout.
- Custom-painted track list with rounded rows, hover states, album thumbnails and an animated "equalizer" for the playing track.
- Round cover widget with a spinning-vinyl fallback for tracks without artwork; responsive layout for compact windows.
- Search, shortcuts (`Space`, `← →`, `↑ ↓`, `Ctrl+O/F/S/R/Q`, `Esc`) and hardware media keys.
- "Run at Windows startup" toggle, "Always on top", and a dark Windows title bar.
- `--diagnose` (audio device report + decode test) and `--smoketest` (end-to-end playback check) command-line switches.
- PyInstaller spec (`Nava.spec`), one-click `build.bat`, multi-size `nava.ico` generator,
  screenshot tooling and a GitHub Actions workflow that builds `Nava.exe` on Windows runners.

[1.0.0]: https://github.com/<your-username>/nava-player/releases/tag/v1.0.0
