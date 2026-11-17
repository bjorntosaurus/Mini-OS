"""Desktop wallpapers: procedurally painted (sharp at any resolution, nothing to download) + your own images."""
import math
import os
import random

from PySide6.QtCore import QPointF, QRectF, QSize, Qt
from PySide6.QtGui import (QBrush, QColor, QImage, QLinearGradient, QPainter, QPainterPath, QPen, QPixmap, QRadialGradient)

MODES = ["Fill", "Fit", "Stretch", "Center", "Tile"]


def _vgrad(w, h, stops, y0=0.0, y1=1.0):
    g = QLinearGradient(0, h * y0, 0, h * y1)
    for pos, col in stops:
        g.setColorAt(pos, QColor(col))
    return g


def _hill(p, w, h, y, amp, phase, top, bottom, ymax=None):
    path = QPainterPath(QPointF(0, h))
    path.lineTo(0, h * y)
    n = 6
    for i in range(1, n + 1):
        x = w * i / n
        yy = h * (y + amp * math.sin(phase + i * 1.3))
        cx = w * (i - 0.5) / n
        cy = h * (y + amp * math.sin(phase + i * 1.3 - 1.9) * 1.4)
        path.quadTo(cx, cy, x, yy)
    path.lineTo(w, h)
    path.closeSubpath()
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(_vgrad(w, h, [(0, top), (1, bottom)], y - amp * 2, 1.0)))
    p.drawPath(path)


def _cloud(p, cx, cy, size, rnd, alpha=215):
    for _ in range(9):
        rx = size * rnd.uniform(0.35, 0.75)
        ry = rx * rnd.uniform(0.38, 0.55)
        x = cx + rnd.uniform(-size, size) * 0.9
        y = cy + rnd.uniform(-size, size) * 0.12
        g = QRadialGradient(QPointF(x, y), rx)
        g.setColorAt(0, QColor(255, 255, 255, alpha))
        g.setColorAt(0.6, QColor(255, 255, 255, int(alpha * 0.55)))
        g.setColorAt(1, QColor(255, 255, 255, 0))
        p.setBrush(QBrush(g))
        p.setPen(Qt.NoPen)
        p.drawEllipse(QPointF(x, y), rx, ry)


def meadow(p, w, h):
    p.fillRect(0, 0, w, h, QBrush(_vgrad(w, h, [(0, "#0e5fd0"), (0.45, "#4b9bea"), (0.7, "#a9d3f6")], 0, 0.7)))
    rnd = random.Random(11)
    for _ in range(9):
        _cloud(p, rnd.uniform(0, w), rnd.uniform(h * 0.04, h * 0.42), rnd.uniform(w * 0.05, w * 0.12), rnd)
    _hill(p, w, h, 0.62, 0.035, 0.4, "#79b83a", "#3f8a1c")
    _hill(p, w, h, 0.72, 0.045, 2.2, "#8ed23a", "#2f7d12")
    _hill(p, w, h, 0.86, 0.04, 4.1, "#6fbd2c", "#276e0d")


def sunset(p, w, h):
    p.fillRect(0, 0, w, h, QBrush(_vgrad(w, h, [(0, "#2b1055"), (0.45, "#b83a7a"), (0.72, "#ff8c4b"), (1, "#ffd27a")], 0, 0.78)))
    g = QRadialGradient(QPointF(w * 0.68, h * 0.62), h * 0.22)
    g.setColorAt(0, QColor("#fff3c4")); g.setColorAt(0.35, QColor(255, 214, 120, 230)); g.setColorAt(1, QColor(255, 160, 80, 0))
    p.setBrush(QBrush(g)); p.setPen(Qt.NoPen)
    p.drawEllipse(QPointF(w * 0.68, h * 0.62), h * 0.22, h * 0.22)
    _hill(p, w, h, 0.70, 0.04, 1.0, "#5b2a6e", "#2a1040")
    _hill(p, w, h, 0.82, 0.05, 3.3, "#2e1450", "#150822")


def midnight(p, w, h):
    p.fillRect(0, 0, w, h, QBrush(_vgrad(w, h, [(0, "#03061a"), (0.6, "#0b2150"), (1, "#14438a")])))
    rnd = random.Random(5)
    p.setPen(Qt.NoPen)
    for _ in range(int(w * h / 4500)):
        a = rnd.randint(90, 255)
        p.setBrush(QColor(255, 255, 255, a))
        r = rnd.choice((0.6, 0.8, 1.0, 1.3))
        p.drawEllipse(QPointF(rnd.uniform(0, w), rnd.uniform(0, h * 0.8)), r, r)
    g = QRadialGradient(QPointF(w * 0.8, h * 0.2), h * 0.1)
    g.setColorAt(0, QColor("#fffbe8")); g.setColorAt(0.7, QColor("#f2eec8")); g.setColorAt(1, QColor(242, 238, 200, 0))
    p.setBrush(QBrush(g)); p.drawEllipse(QPointF(w * 0.8, h * 0.2), h * 0.1, h * 0.1)
    _hill(p, w, h, 0.76, 0.04, 0.9, "#0a1c3d", "#040a1c")
    _hill(p, w, h, 0.88, 0.04, 3.0, "#06122b", "#02060f")


def neoblocks(p, w, h):
    p.fillRect(0, 0, w, h, QColor("#f4f4e9"))
    p.setPen(QPen(QColor(29, 42, 34, 28), 1))
    for x in range(0, w, 40):
        p.drawLine(x, 0, x, h)
    for y in range(0, h, 40):
        p.drawLine(0, y, w, y)
    cols = ["#c4f06a", "#ffa3c4", "#c5b3f2", "#ffcc62", "#84d9e0", "#ff9970", "#a9b4f9"]
    rnd = random.Random(3)
    ink = QColor("#1d2a22")
    for i in range(11):
        bw, bh = rnd.uniform(w * 0.08, w * 0.2), rnd.uniform(h * 0.1, h * 0.26)
        x, y = rnd.uniform(0, w - bw), rnd.uniform(0, h - bh)
        r = QRectF(round(x / 40) * 40, round(y / 40) * 40, round(bw / 40) * 40 or 80, round(bh / 40) * 40 or 80)
        p.setPen(Qt.NoPen); p.setBrush(ink)
        p.drawRect(r.translated(8, 8))
        p.setPen(QPen(ink, 3)); p.setBrush(QColor(cols[i % len(cols)]))
        p.drawRect(r)


def teal(p, w, h):
    p.fillRect(0, 0, w, h, QColor("#286d72"))
    p.setPen(QPen(QColor(255, 255, 255, 14), 1))
    for x in range(0, w, 48):
        p.drawLine(x, 0, x, h)
    for y in range(0, h, 48):
        p.drawLine(0, y, w, y)


def classic(p, w, h):
    p.fillRect(0, 0, w, h, QBrush(_vgrad(w, h, [(0, "#245edb"), (1, "#0a3aa8")])))


BUILTIN = {"meadow": ("Meadow", meadow), "sunset": ("Sunset", sunset), "midnight": ("Midnight", midnight),
           "neo": ("Neo blocks", neoblocks), "teal": ("Kernel teal", teal), "classic": ("Classic blue", classic)}
DEFAULT = "builtin:meadow"
_IMG_CACHE = {}


def _load_image(path):
    if path not in _IMG_CACHE:
        img = QImage(path)
        if not img.isNull() and max(img.width(), img.height()) > 3200:
            img = img.scaled(3200, 3200, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        _IMG_CACHE.clear()
        _IMG_CACHE[path] = img
    return _IMG_CACHE[path]


def render(spec, mode, size: QSize) -> QPixmap:
    """Paint the wallpaper `spec` ('builtin:<id>' or 'file:<path>') into a pixmap of the given size."""
    w, h = max(1, size.width()), max(1, size.height())
    pm = QPixmap(w, h)
    p = QPainter(pm)
    p.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)
    kind, _, val = spec.partition(":")
    if kind == "file":
        img = _load_image(val)
        if img.isNull():
            p.end()                      # finish painting before the pixmap is discarded
            return render(DEFAULT, mode, size)
        p.fillRect(0, 0, w, h, QColor("#0a2a6b"))
        iw, ih = img.width(), img.height()
        if mode == "Stretch":
            p.drawImage(QRectF(0, 0, w, h), img)
        elif mode == "Tile":
            for x in range(0, w, iw):
                for y in range(0, h, ih):
                    p.drawImage(x, y, img)
        elif mode == "Center":
            p.drawImage((w - iw) // 2, (h - ih) // 2, img)
        else:
            k = max(w / iw, h / ih) if mode == "Fill" else min(w / iw, h / ih)
            tw, th = iw * k, ih * k
            p.drawImage(QRectF((w - tw) / 2, (h - th) / 2, tw, th), img)
    else:
        BUILTIN.get(val, BUILTIN["meadow"])[1](p, w, h)
    p.end()
    return pm


# ---------------------------------------------------------------- picture library
from gui.widgets.common import ROOT          # noqa: E402

IMG_EXT = (".png", ".jpg", ".jpeg", ".bmp", ".gif", ".webp")
WALLPAPER_DIR = os.path.join(ROOT, "wallpapers")


def is_image(path):
    return path.lower().endswith(IMG_EXT)


def folder_images():
    """Pictures dropped into the project's wallpapers/ folder."""
    try:
        return sorted(os.path.join(WALLPAPER_DIR, f) for f in os.listdir(WALLPAPER_DIR) if is_image(f))
    except OSError:
        return []


def parse_library(text):
    """Stored library string ('|' separated paths) -> list of paths that still exist."""
    return [p for p in text.split("|") if p and os.path.isfile(p)]


def join_library(paths):
    return "|".join(dict.fromkeys(paths))
