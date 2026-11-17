"""Rough repaint benchmark: python tools/bench.py  (offscreen)"""
import os, sys, time
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from PySide6.QtWidgets import QApplication
from main import load_fonts
app = QApplication([]); app.setStyle("Fusion"); load_fonts()
from gui.xp_desktop import XPDesktop
d = XPDesktop(); d.resize(1316, 913); d.show(); app.processEvents()
for i in (1, 2, 4, 7): d.open_app(i)
app.processEvents()
def t(label, fn, n=15):
    fn(); s = time.perf_counter()
    for _ in range(n): fn()
    print(f"{label:28s}{(time.perf_counter() - s) / n * 1000:7.1f} ms")
t("full repaint (4 windows)", lambda: (d.repaint(), app.processEvents()))
w = d.windows[7]
def drag():
    w.move(w.x() + 3, w.y() + 2); app.processEvents()
t("drag one window 1 step", drag)
t("resize main window", lambda: (d.resize(d.width() + (7 if d.width() < 1400 else -80), 913), app.processEvents()))
