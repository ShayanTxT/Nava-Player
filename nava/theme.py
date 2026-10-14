"""Themes: cozy palettes + the global stylesheet."""
from __future__ import annotations

from dataclasses import dataclass
from string import Template


@dataclass(frozen=True)
class Theme:
    key: str
    name_fa: str
    name_en: str
    bg: str            # window background (top of gradient)
    bg2: str           # window background (bottom of gradient)
    panel: str         # card background
    panel2: str        # secondary card background / list alternate
    border: str
    text: str
    dim: str
    accent: str
    accent2: str       # gradient end for accent
    on_accent: str     # text/icon color on top of accent
    glow: str          # rgba() used for soft shadows

    def name(self, lang: str) -> str:
        return self.name_fa if lang == "fa" else self.name_en


THEMES = [
    Theme(
        key="coffee", name_fa="قهوه و کارامل", name_en="Coffee & Caramel",
        bg="#171210", bg2="#241a15", panel="#231a15", panel2="#2c211a",
        border="#3b2d24", text="#f4ece4", dim="#a8917f",
        accent="#e8a87c", accent2="#d2803f", on_accent="#22160e",
        glow="rgba(232, 168, 124, 60)",
    ),
    Theme(
        key="forest", name_fa="جنگل نیمه‌شب", name_en="Midnight Forest",
        bg="#0d1411", bg2="#16211c", panel="#151f1a", panel2="#1d2923",
        border="#27372e", text="#e8f1ea", dim="#8fa79a",
        accent="#7fd1a5", accent2="#43a17a", on_accent="#0b1710",
        glow="rgba(127, 209, 165, 55)",
    ),
    Theme(
        key="indigo", name_fa="شب نیلی", name_en="Indigo Night",
        bg="#0f1120", bg2="#1a1d33", panel="#181b2f", panel2="#212440",
        border="#2b3050", text="#eaecf8", dim="#9198bd",
        accent="#a495ff", accent2="#6f5ae0", on_accent="#12102a",
        glow="rgba(164, 149, 255, 55)",
    ),
    Theme(
        key="sunset", name_fa="غروب گرم", name_en="Warm Sunset",
        bg="#1b0f16", bg2="#2a1622", panel="#261520", panel2="#31202c",
        border="#3f2436", text="#f8ebf1", dim="#b58f9f",
        accent="#ff9db4", accent2="#ea6f8f", on_accent="#2a1018",
        glow="rgba(255, 157, 180, 55)",
    ),
]

THEME_BY_KEY = {t.key: t for t in THEMES}
DEFAULT_THEME = THEMES[0]


def next_theme(key: str) -> Theme:
    keys = [t.key for t in THEMES]
    try:
        idx = keys.index(key)
    except ValueError:
        idx = 0
    return THEMES[(idx + 1) % len(THEMES)]


QSS = Template("""
* { outline: none; }

QWidget {
    color: $text;
    font-family: "Segoe UI", "Vazirmatn", "Tahoma", "Noto Sans Arabic", sans-serif;
    font-size: 13px;
}

QMainWindow, #Root {
    background: qlineargradient(x1:0, y1:0, x2:0.6, y2:1,
                stop:0 $bg, stop:1 $bg2);
}

#Header, #Panel, #Card {
    background: $panel;
    border: 1px solid $border;
    border-radius: 18px;
}

#NowPanel { background: transparent; }

QLabel { background: transparent; }

#AppName { font-size: 19px; font-weight: 700; color: $text; }
#AppTag  { font-size: 11px; color: $dim; }
#SectionTitle { font-size: 13px; font-weight: 700; color: $dim; letter-spacing: 1px; }
#TrackTitle { font-size: 21px; font-weight: 700; color: $text; }
#TrackArtist { font-size: 14px; color: $accent; }
#TrackAlbum { font-size: 12px; color: $dim; }
#Time { font-size: 11px; color: $dim; }
#Status { font-size: 11px; color: $dim; }
#Path { font-size: 11px; color: $dim; }

QLineEdit {
    background: $panel2;
    border: 1px solid $border;
    border-radius: 12px;
    padding: 8px 14px 8px 14px;
    selection-background-color: $accent;
    selection-color: $on_accent;
}
QLineEdit:focus { border: 1px solid $accent; }

QPushButton {
    background: $panel2;
    border: 1px solid $border;
    border-radius: 12px;
    padding: 8px 16px;
    color: $text;
    font-weight: 600;
}
QPushButton:hover { background: $border; }
QPushButton:pressed { background: $panel; }
QPushButton#Accent {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 $accent, stop:1 $accent2);
    color: $on_accent;
    border: none;
}
QPushButton#Accent:hover { background: $accent; }

QMenu {
    background: $panel;
    border: 1px solid $border;
    border-radius: 12px;
    padding: 6px;
}
QMenu::item {
    padding: 7px 26px 7px 22px;
    border-radius: 8px;
    color: $text;
}
QMenu::item:selected { background: $panel2; color: $accent; }
QMenu::separator { height: 1px; background: $border; margin: 5px 10px; }
QMenu::indicator { width: 16px; height: 16px; }

QToolTip {
    background: $panel;
    color: $text;
    border: 1px solid $border;
    padding: 5px 9px;
    border-radius: 8px;
}

QListWidget {
    background: transparent;
    border: none;
    padding: 6px 10px 6px 10px;
}
QListWidget::item { border-radius: 12px; }

QScrollBar:vertical {
    background: transparent; width: 10px; margin: 4px 2px 4px 2px;
}
QScrollBar::handle:vertical {
    background: $border; min-height: 40px; border-radius: 5px;
}
QScrollBar::handle:vertical:hover { background: $accent2; }
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }

QSlider::groove:horizontal {
    height: 6px; border-radius: 3px; background: $panel2; border: 1px solid $border;
}
QSlider::sub-page:horizontal {
    height: 6px; border-radius: 3px;
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 $accent2, stop:1 $accent);
}
QSlider::handle:horizontal {
    width: 13px; height: 13px; margin: -5px 0; border-radius: 7px;
    background: $accent; border: 2px solid $panel;
}
QSlider::handle:horizontal:hover { background: #ffffff; }

#SeekSlider::groove:horizontal { height: 7px; border-radius: 4px; }
#SeekSlider::sub-page:horizontal { height: 7px; border-radius: 4px; }
#SeekSlider::handle:horizontal { width: 15px; height: 15px; margin: -5px 0; border-radius: 8px; }

#Card QLabel { color: $text; }
QSplitter::handle { background: transparent; }
""")
