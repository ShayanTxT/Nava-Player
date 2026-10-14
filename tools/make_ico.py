"""Generate nava.ico (multi-size, PNG-compressed entries) for the Windows build."""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from PySide6.QtGui import QGuiApplication, QPixmap  # noqa: E402
from nava.icons import app_icon_pixmap                # noqa: E402

app = QGuiApplication(sys.argv)
SIZES = [16, 24, 32, 48, 64, 128, 256]
PNG_DIR = os.path.join(ROOT, "tools", "_icon_pngs")
os.makedirs(PNG_DIR, exist_ok=True)

pngs = []
for size in SIZES:
    pm = app_icon_pixmap(size, "#e8a87c", "#d2803f", "#22160e", 1.0)
    path = os.path.join(PNG_DIR, f"{size}.png")
    pm.save(path, "PNG")
    pngs.append(path)

out = os.path.join(ROOT, "nava.ico")
entries, payloads = [], b""
offset = 6 + 16 * len(SIZES)
for size, path in zip(SIZES, pngs):
    with open(path, "rb") as fh:
        data = fh.read()
    entries.append(struct.pack("<BBBBHHII", size if size < 256 else 0,
                               size if size < 256 else 0, 0, 0, 1, 32, len(data), offset))
    offset += len(data)
    payloads += data

with open(out, "wb") as fh:
    fh.write(struct.pack("<HHH", 0, 1, len(SIZES)))
    fh.write(b"".join(entries))
    fh.write(payloads)
print("wrote", out, os.path.getsize(out), "bytes")
