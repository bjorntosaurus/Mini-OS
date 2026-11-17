import os, sys
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)
from PySide6.QtWidgets import QApplication
from main import load_fonts
app = QApplication([]); app.setStyle("Fusion"); load_fonts()
from gui.xp_desktop import XPDesktop
w = XPDesktop(); w.resize(1316, 913); w.show(); app.processEvents(); app.processEvents()
w.wall.rebuild(); app.processEvents()
w.grab().save("/tmp/xp_home.png")
w.open_app(1); w.windows["explorer"].hide(); app.processEvents(); w.grab().save("/tmp/xp_cpu.png")
from gui.wallpapers import BUILTIN
from PySide6.QtCore import QSize
from gui.wallpapers import render
from PIL import Image
ims = []
for k in BUILTIN:
    render(f"builtin:{k}", "Fill", QSize(440, 275)).save(f"/tmp/wp_{k}.png"); ims.append(Image.open(f"/tmp/wp_{k}.png"))
m = Image.new("RGB", (440 * 3, 275 * 2))
for i, im in enumerate(ims): m.paste(im, ((i % 3) * 440, (i // 3) * 275))
m.save("/tmp/wp_all.png")
