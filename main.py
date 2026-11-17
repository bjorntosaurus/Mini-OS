"""Kernel — Operating System Simulator.  Run:  python main.py            (Windows-XP style desktop, default)
                                              python main.py --skin 98   (Kernel / 98 desktop)"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)

from PySide6.QtGui import QFontDatabase
from PySide6.QtWidgets import QApplication


def load_fonts():
    d = os.path.join(ROOT, "assets", "fonts")
    if os.path.isdir(d):
        for f in os.listdir(d):
            if f.lower().endswith((".ttf", ".otf")):
                QFontDatabase.addApplicationFont(os.path.join(d, f))


def create_skin(name):
    if name == "98":
        from gui.main_window import MainWindow
        return MainWindow()
    from gui.xp_desktop import XPDesktop
    return XPDesktop()


class Launcher:
    """Owns both desktop skins and switches between them (they share the same preferences)."""

    def __init__(self, first):
        from gui.settings import get_prefs
        self.prefs, self.wins, self.current = get_prefs(), {}, None
        self.show(first, initial=True)

    def show(self, name, initial=False):
        old = self.wins.get(self.current)
        if name not in self.wins:
            w = create_skin(name)
            w.skinRequested.connect(self.show)
            self.wins[name] = w
        new = self.wins[name]
        if old is not None:
            new.setGeometry(old.geometry())
            old.hide()
        else:
            new.resize(1316, 913)
        new.show()
        self.current = name
        self.prefs.values["skin"] = name


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skin", choices=["xp", "98"], default=None)
    args, qt_args = ap.parse_known_args()
    app = QApplication([sys.argv[0]] + qt_args)
    app.setStyle("Fusion")
    app.setApplicationName("Kernel OS Simulator")
    load_fonts()
    from gui.settings import get_prefs
    skin = args.skin or ("xp" if get_prefs()["skin"] not in ("xp", "98") else get_prefs()["skin"])
    launcher = Launcher(skin)
    code = app.exec()
    get_prefs().save()
    return code


if __name__ == "__main__":
    sys.exit(main())
