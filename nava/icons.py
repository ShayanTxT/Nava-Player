"""Vector icons drawn from inline SVG (no external files needed)."""
from __future__ import annotations

from functools import lru_cache

from PySide6.QtCore import QByteArray, QRectF, Qt
from PySide6.QtGui import QPainter, QPen, QPixmap

_STROKE = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" '
           'stroke="{c}" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round">{d}</svg>')
_FILL = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="{c}">{d}</svg>')

_STROKE_ICONS = {
    "play": '<path d="M7 4.8 18.5 12 7 19.2z" fill="{c}" stroke="{c}" stroke-width="1.6"/>',
    "pause": '<rect x="6.5" y="5" width="3.6" height="14" rx="1.6" fill="{c}" stroke="none"/>'
             '<rect x="13.9" y="5" width="3.6" height="14" rx="1.6" fill="{c}" stroke="none"/>',
    "next": '<path d="M6 5.6 14.6 12 6 18.4z" fill="{c}" stroke="{c}" stroke-width="1.6"/>'
            '<rect x="16.2" y="5.2" width="2.6" height="13.6" rx="1.3" fill="{c}" stroke="none"/>',
    "prev": '<path d="M18 5.6 9.4 12 18 18.4z" fill="{c}" stroke="{c}" stroke-width="1.6"/>'
            '<rect x="5.2" y="5.2" width="2.6" height="13.6" rx="1.3" fill="{c}" stroke="none"/>',
    "shuffle": '<path d="M16 3h5v5"/><path d="M4 20 21 3"/><path d="M21 16v5h-5"/>'
               '<path d="M15 15l6 6"/><path d="M4 4l5 5"/>',
    "repeat": '<path d="M17 2.5l3.5 3.5L17 9.5"/>'
              '<path d="M3.5 11.5V11a4 4 0 0 1 4-4h13"/>'
              '<path d="M7 21.5 3.5 18 7 14.5"/>'
              '<path d="M20.5 12.5v.5a4 4 0 0 1-4 4h-13"/>',
    "repeat_one": '<path d="M17 2.5l3.5 3.5L17 9.5"/>'
                  '<path d="M3.5 11.5V11a4 4 0 0 1 4-4h13"/>'
                  '<path d="M7 21.5 3.5 18 7 14.5"/>'
                  '<path d="M20.5 12.5v.5a4 4 0 0 1-4 4h-13"/>'
                  '<path d="M11.4 10.6l1.3-.9v4.6" stroke-width="1.7"/>',
    "volume": '<path d="M11 5 6.5 8.6H3.4v6.8h3.1L11 19z"/>'
              '<path d="M15.2 9.2a4 4 0 0 1 0 5.6"/><path d="M18 6.6a7.8 7.8 0 0 1 0 10.8"/>',
    "volume_low": '<path d="M11 5 6.5 8.6H3.4v6.8h3.1L11 19z"/><path d="M15.2 9.2a4 4 0 0 1 0 5.6"/>',
    "mute": '<path d="M11 5 6.5 8.6H3.4v6.8h3.1L11 19z"/>'
            '<path d="M16 9.5l5 5"/><path d="M21 9.5l-5 5"/>',
    "folder": '<path d="M3 7.2A2.2 2.2 0 0 1 5.2 5h3.4a2 2 0 0 1 1.5.7l1 1.1h7.7A2.2 2.2 0 0 1 21 9v8.3A2.2 2.2 0 0 1 18.8 19.5H5.2A2.2 2.2 0 0 1 3 17.3z"/>',
    "search": '<circle cx="10.8" cy="10.8" r="6.3"/><path d="M15.5 15.5 20.5 20.5"/>',
    "palette": '<circle cx="12" cy="12" r="8.6"/>'
               '<circle cx="8.6" cy="9.6" r="1.15" fill="{c}" stroke="none"/>'
               '<circle cx="12" cy="8.2" r="1.15" fill="{c}" stroke="none"/>'
               '<circle cx="15.4" cy="9.6" r="1.15" fill="{c}" stroke="none"/>'
               '<circle cx="9.4" cy="14.6" r="1.15" fill="{c}" stroke="none"/>',
    "gear": '<circle cx="12" cy="12" r="3.1"/>'
            '<path d="M19.4 15a1.7 1.7 0 0 0 .34 1.87l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.7 1.7 0 0 0-1.87-.34 1.7 1.7 0 0 0-1.03 1.56V21a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 8.9 19.3a1.7 1.7 0 0 0-1.87.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-1.56-1.03H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.7 8.9a1.7 1.7 0 0 0-.34-1.87l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1.03-1.56V3a2 2 0 1 1 4 0v.09A1.7 1.7 0 0 0 15 4.7a1.7 1.7 0 0 0 1.87-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.3 9v.06a1.7 1.7 0 0 0 1.56 1.03H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51 1.03z"/>',
    "minimize": '<path d="M5 12h14"/>',
    "close": '<path d="M6 6l12 12"/><path d="M18 6 6 18"/>',
    "pin": '<path d="M9 3h6l-.7 5.2 3 3.3H6.7l3-3.3z"/><path d="M12 11.5V21"/>',
    "note": '<path d="M9.3 6.9 18.6 4l.45 2.2-9.3 2.9z" fill="{c}" stroke="none"/>'
            '<rect x="9.3" y="6.3" width="1.7" height="10.6" rx="0.85" fill="{c}" stroke="none"/>'
            '<rect x="17.3" y="3.7" width="1.7" height="10.0" rx="0.85" fill="{c}" stroke="none"/>'
            '<g transform="rotate(-24 7.5 17.3)">'
            '<ellipse cx="7.5" cy="17.3" rx="3.4" ry="2.65" fill="{c}" stroke="none"/></g>'
            '<g transform="rotate(-24 15.5 14.3)">'
            '<ellipse cx="15.5" cy="14.3" rx="3.4" ry="2.65" fill="{c}" stroke="none"/></g>',
    "list": '<path d="M8 6h12"/><path d="M8 12h12"/><path d="M8 18h12"/>'
            '<circle cx="4" cy="6" r="1.2" fill="{c}" stroke="none"/>'
            '<circle cx="4" cy="12" r="1.2" fill="{c}" stroke="none"/>'
            '<circle cx="4" cy="18" r="1.2" fill="{c}" stroke="none"/>',
    "trash": '<path d="M4 7h16"/><path d="M9.5 7V4.8h5V7"/>'
             '<path d="M6.5 7l.8 12.2h9.4L17.5 7"/><path d="M10 11v5"/><path d="M14 11v5"/>',
    "heart": '<path d="M12 20s-7.5-4.7-7.5-9.6A4.4 4.4 0 0 1 12 7.4a4.4 4.4 0 0 1 7.5 3c0 4.9-7.5 9.6-7.5 9.6z"/>',
    "clock": '<circle cx="12" cy="12" r="8.6"/><path d="M12 7.5V12l3 2"/>',
    "expand": '<path d="M9 3H3v6"/><path d="M15 21h6v-6"/><path d="M3 3l7 7"/><path d="M21 21l-7-7"/>',
}


def app_icon_pixmap(size: int = 256, accent: str = "#e8a87c", accent2: str = "#d2803f",
                   bg: str = "#22160e", dpr: float = 1.0) -> QPixmap:
    """The Nava app icon: a warm vinyl disc with a music note on it."""
    from PySide6.QtGui import QColor, QRadialGradient

    px = QPixmap(int(size * dpr), int(size * dpr))
    px.setDevicePixelRatio(dpr)
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing, True)
    painter.setRenderHint(QPainter.SmoothPixmapTransform, True)

    side = size * dpr
    rect = QRectF(side * 0.03, side * 0.03, side * 0.94, side * 0.94)
    grad = QRadialGradient(rect.center(), side * 0.52)
    grad.setColorAt(0.0, QColor(accent))
    grad.setColorAt(1.0, QColor(accent2))
    painter.setPen(Qt.NoPen)
    painter.setBrush(grad)
    painter.drawEllipse(rect)

    painter.setBrush(Qt.NoBrush)
    painter.setPen(QPen(QColor(0, 0, 0, 46), max(1.0, side * 0.012)))
    for factor in (0.86, 0.74, 0.62):
        rr = side * 0.47 * factor
        painter.drawEllipse(QRectF(rect.center().x() - rr, rect.center().y() - rr, rr * 2, rr * 2))

    glyph = int(side * 0.60)
    note = _note_pixmap(bg, glyph, dpr)
    painter.drawPixmap(int((side - glyph) / 2), int((side - glyph) / 2), note)
    painter.end()
    return px


def _note_pixmap(color: str, size: int, dpr: float) -> QPixmap:
    from PySide6.QtSvg import QSvgRenderer

    body = _STROKE_ICONS["note"]
    svg = _STROKE.format(c=color, w=1.0, d=body.format(c=color))
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    px = QPixmap(int(size * dpr), int(size * dpr))
    px.setDevicePixelRatio(dpr)
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter, QRectF(0, 0, size * dpr, size * dpr))
    painter.end()
    return px


@lru_cache(maxsize=512)
def icon_pixmap(name: str, color: str, size: int = 22, width: float = 1.9, dpr: float = 1.0) -> QPixmap:
    from PySide6.QtSvg import QSvgRenderer

    body = _STROKE_ICONS.get(name, _STROKE_ICONS["note"])
    svg = _STROKE.format(c=color, w=width, d=body.format(c=color))
    renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
    px = QPixmap(int(size * dpr), int(size * dpr))
    px.setDevicePixelRatio(dpr)
    px.fill(Qt.transparent)
    painter = QPainter(px)
    painter.setRenderHint(QPainter.Antialiasing, True)
    renderer.render(painter, QRectF(0, 0, size * dpr, size * dpr))
    painter.end()
    return px
