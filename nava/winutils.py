"""Windows-specific helpers: autostart entry, taskbar/thumbnail integration."""
from __future__ import annotations

import os
import sys

from .config import is_windows

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
APP_KEY = "NavaPlayer"


def _startup_folder() -> str:
    appdata = os.environ.get("APPDATA") or os.path.expanduser("~")
    return os.path.join(appdata, "Microsoft", "Windows", "Start Menu", "Programs", "Startup")


def _launch_command() -> str:
    if getattr(sys, "frozen", False):
        return f'"{sys.executable}"'
    script = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "main.py")
    return f'"{sys.executable}" "{script}"'


def autostart_enabled() -> bool:
    if not is_windows():
        return os.path.exists(os.path.join(_startup_folder(), f"{APP_KEY}.bat"))
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_KEY)
            return True
    except Exception:
        return False


def set_autostart(enabled: bool) -> bool:
    """Enable/disable 'run at login'. Uses the registry, falls back to the Startup folder."""
    if not is_windows():
        path = os.path.join(_startup_folder(), f"{APP_KEY}.bat")
        try:
            if enabled:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(f"start \"\" {_launch_command()}\n")
            elif os.path.exists(path):
                os.remove(path)
            return True
        except Exception:
            return False

    try:
        import winreg
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            if enabled:
                winreg.SetValueEx(key, APP_KEY, 0, winreg.REG_SZ, _launch_command())
            else:
                try:
                    winreg.DeleteValue(key, APP_KEY)
                except FileNotFoundError:
                    pass
        return True
    except Exception:
        pass

    # fallback: Startup folder shortcut
    path = os.path.join(_startup_folder(), f"{APP_KEY}.bat")
    try:
        if enabled:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(f"start \"\" {_launch_command()}\n")
        elif os.path.exists(path):
            os.remove(path)
        return True
    except Exception:
        return False


def apply_windows_extras(window):
    """Dark title bar + (best effort) thumbnail toolbar with prev/play/next."""
    if not is_windows():
        return
    try:
        import ctypes
        from ctypes import wintypes

        hwnd = int(window.winId())

        # --- dark title bar ---------------------------------------------------
        try:
            DWMWA_USE_IMMERSIVE_DARK_MODE = 20
            value = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(
                wintypes.HWND(hwnd), DWMWA_USE_IMMERSIVE_DARK_MODE,
                ctypes.byref(value), ctypes.sizeof(value))
        except Exception:
            pass

        # --- thumbnail toolbar (shows on hover over the taskbar icon) ---------
        try:
            class THUMBBUTTON(ctypes.Structure):
                _fields_ = [("dwMask", wintypes.DWORD), ("iId", wintypes.UINT),
                            ("iBitmap", wintypes.UINT), ("hIcon", wintypes.HICON),
                            ("szTip", wintypes.WCHAR * 260), ("dwFlags", wintypes.DWORD)]

            THB_ICON, THB_TOOLTIP, THB_FLAGS = 0x2, 0x4, 0x8
            THBF_ENABLED = 0x0
            WM_COMMAND = 0x0111
            THBN_CLICKED = 0x1800

            user32 = ctypes.windll.user32
            shell32 = ctypes.windll.shell32
            comctl32 = ctypes.windll.comctl32

            class ThumbCallback:
                pass

            window._thumb_buttons = THUMBBUTTON * 3
            buttons = window._thumb_buttons()
            specs = [(1, "prev", "Previous"), (2, "play", "Play / Pause"), (3, "next", "Next")]
            for btn, (bid, _name, tip) in zip(buttons, specs):
                btn.dwMask = THB_TOOLTIP | THB_FLAGS
                btn.iId = bid
                btn.dwFlags = THBF_ENABLED
                btn.szTip = tip

            taskbar = ctypes.c_void_p()
            ctypes.windll.ole32.CoInitialize(None)
            iid = ctypes.c_byte * 16
            import uuid
            class GUID(ctypes.Structure):
                _fields_ = [("d1", wintypes.DWORD), ("d2", wintypes.WORD),
                            ("d3", wintypes.WORD), ("d4", ctypes.c_byte * 8)]

            def guid(text):
                g = GUID()
                ctypes.windll.ole32.CLSIDFromString(ctypes.c_wchar_p(text), ctypes.byref(g))
                return g

            clsid = guid("{56FDF344-FD6D-11d0-958A-006097C9A090}")   # CLSID_TaskbarList
            iid_tbl = guid("{EA1AFB91-9E28-4B86-90E9-9E9F8A5EEA84}")  # ITaskbarList3
            obj = ctypes.c_void_p()
            ctypes.windll.ole32.CoCreateInstance(ctypes.byref(clsid), None, 1,
                                                 ctypes.byref(iid_tbl), ctypes.byref(obj))
            if obj:
                vtbl = ctypes.cast(obj, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p)))[0]
                # ITaskbarList3: HrInit(3) then ThumbBarAddButtons(11)
                HrInit = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p)(vtbl[3])
                HrInit(obj)
                AddButtons = ctypes.WINFUNCTYPE(ctypes.HRESULT, ctypes.c_void_p,
                                                wintypes.HWND, wintypes.UINT,
                                                ctypes.POINTER(THUMBBUTTON))(vtbl[11])
                AddButtons(obj, wintypes.HWND(hwnd), 3, buttons)
        except Exception:
            pass
    except Exception:
        pass
