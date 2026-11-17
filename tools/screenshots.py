"""Render every page to PNG for visual comparison with the Figma export.  python tools/screenshots.py [outdir] [light|dark]"""
import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from PySide6.QtWidgets import QApplication
from main import load_fonts

def run(out, mode):
    app = QApplication([]); app.setStyle("Fusion"); load_fonts()
    from gui.main_window import MainWindow
    w = MainWindow(); w.resize(1316, 913); w.show(); app.processEvents()
    w.prefs.update(mode=mode)
    os.makedirs(out, exist_ok=True)
    for i in range(10):
        w.open_page(i); app.processEvents()
        w.grab().save(os.path.join(out, f"{mode}_{i}.png"))
if __name__ == "__main__":
    run(sys.argv[1] if len(sys.argv) > 1 else "/tmp/shots", sys.argv[2] if len(sys.argv) > 2 else "light")
