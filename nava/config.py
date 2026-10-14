"""Config + small filesystem helpers."""
from __future__ import annotations

import json
import os
import sys

APP_DIR_NAME = "NavaPlayer"


def is_windows() -> bool:
    return sys.platform.startswith("win")


def config_dir() -> str:
    if is_windows():
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    path = os.path.join(base, APP_DIR_NAME)
    os.makedirs(path, exist_ok=True)
    return path


def resource_path(*parts: str) -> str:
    """Path to a bundled resource (works inside a PyInstaller onefile build)."""
    base = getattr(sys, "_MEIPASS", None)
    if base:
        return os.path.join(base, *parts)
    here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(here, *parts)


DEFAULTS = {
    "lang": "en",          # en | fa  (switch it from Menu -> Language)
    "theme": "coffee",
    "folder": "",
    "recursive": True,
    "volume": 72,
    "shuffle": False,
    "repeat": "off",          # off | all | one
    "last_index": 0,
    "minimize_to_tray": True,
    "always_on_top": False,
    "autostart": False,
    "tray_hint_shown": False,
    "geometry": None,         # base64 of QByteArray
}


class Config(dict):
    def __init__(self, path: str | None = None):
        super().__init__(DEFAULTS)
        self.path = path or os.path.join(config_dir(), "config.json")
        self.load()

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                data = json.load(fh)
            if isinstance(data, dict):
                for key in DEFAULTS:
                    if key in data:
                        self[key] = data[key]
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            tmp = self.path + ".tmp"
            with open(tmp, "w", encoding="utf-8") as fh:
                json.dump(dict(self), fh, ensure_ascii=False, indent=2)
            os.replace(tmp, self.path)
        except Exception:
            pass
