@echo off
REM ============================================================
REM  Nava Player - build a single-file Windows executable
REM  Just double-click this file (needs Python 3.10+ in PATH)
REM ============================================================
setlocal
cd /d "%~dp0"

echo.
echo ============================================================
echo   Nava Player - building Nava.exe
echo   folder: %CD%
echo ============================================================
echo.

echo [1/3] Checking Python...
python --version 2>nul || goto :nopython
python -m pip install --quiet --upgrade pip
if exist requirements.txt (
    python -m pip install --quiet -r requirements.txt pyinstaller
) else (
    python -m pip install --quiet "PySide6>=6.5,<6.9" mutagen pyinstaller
)
if errorlevel 1 goto :pipfail

echo [2/3] Preparing the application icon...
if exist tools\make_ico.py (
    python tools\make_ico.py
) else (
    echo       tools\make_ico.py not found - using the existing nava.ico
)

echo [3/3] Building dist\Nava.exe  (this takes 1-3 minutes)...
python -m PyInstaller --noconfirm --clean --log-level WARN Nava.spec
if errorlevel 1 goto :buildfail

echo.
echo ============================================================
echo   Done!  Your executable is here:
echo       %CD%\dist\Nava.exe
echo.
echo   Tip: run   dist\Nava.exe --diagnose   if a PC has no sound.
echo ============================================================
echo.
pause
exit /b 0

:nopython
echo.
echo *** Python was not found. ***
echo.
echo  1. Download "Python 3.11 (64-bit)" from  https://www.python.org/downloads/
echo  2. In the installer, TICK "Add python.exe to PATH" (important!)
echo  3. Close this window, open it again and double-click build.bat
echo.
echo  (If Python is installed, try the command  py -3  instead of  python.)
echo.
pause
exit /b 1

:pipfail
echo.
echo *** Installing requirements failed. ***
echo  Check your internet connection / proxy and run:
echo      python -m pip install -r requirements.txt pyinstaller
echo.
pause
exit /b 1

:buildfail
echo.
echo *** PyInstaller failed. ***
echo  Scroll up in this window to read the error.
echo  Common fix:  python -m pip install --upgrade pyinstaller
echo  If the window closed too fast, run build.bat from a Command Prompt
echo  (cmd.exe) so you can read the messages.
echo.
pause
exit /b 1
