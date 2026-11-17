"""Home ("My computer") and Settings pages."""
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout

from gui.pages.base import BasePage
from gui.settings import ACCENTS
from gui.widgets.charts import ThemePreview
from gui.widgets.common import ClickableFrame, icon_path, mk_label

APPS = [  # key, title, subtitle, bar colour, nav label
    ("cpu", "CPU scheduling", "Give every process a turn.", "#c4f06a"),
    ("bankers", "Banker’s algorithm", "Find a safe way forward.", "#ffa3c4"),
    ("paging", "Paging", "Map pages into frames.", "#c5b3f2"),
    ("pagerep", "Page replacement", "Make room for what’s next.", "#ffcc62"),
    ("segmentation", "Segmentation", "Put memory into segments.", "#84d9e0"),
    ("fragmentation", "Fragmentation", "See where memory is lost.", "#ff9970"),
    ("disk", "Disk scheduling", "Take the shortest route.", "#a9b4f9"),
    ("multiprogramming", "Multiprogramming", "Keep your CPU busy.", "#c4f06a"),
]
ICON_FILE = {"cpu": "cpu", "bankers": "bankers", "paging": "paging", "pagerep": "pagerep", "segmentation": "segmentation",
             "fragmentation": "fragmentation", "disk": "disk", "multiprogramming": "multiprogramming"}


class SidebarPage(BasePage):
    navigate = Signal(int)
    NAV_INDEX = 0

    def wire_sidebar(self):
        w = self.w
        w.navHome.clicked.connect(lambda: self.navigate.emit(0))
        w.navSettings.clicked.connect(lambda: self.navigate.emit(9))
        for i, (key, *_r) in enumerate(APPS):
            b = getattr(w, f"nav{i}")
            b.setIcon(QIcon(icon_path(ICON_FILE[key])))
            b.setIconSize(QSize(22, 22))
            b.setText("  " + b.text())
            b.clicked.connect(lambda _=False, i=i: self.navigate.emit(i + 1))
        w.navSettings.setIcon(QIcon(icon_path("settings")))
        w.navSettings.setIconSize(QSize(20, 20))
        w.navSettings.setText("  Settings")
        self.mark_nav()

    def mark_nav(self):
        w = self.w
        w.navHome.setChecked(self.NAV_INDEX == 0)
        w.navSettings.setChecked(self.NAV_INDEX == 9)
        for i in range(8):
            getattr(w, f"nav{i}").setChecked(False)

    def themed(self):
        pass


class HomePage(SidebarPage):
    UI = "home.ui"
    KEY = "home"
    TITLE = "My computer — Kernel / 98"
    PATH = "kernel98 / home"
    NAV_INDEX = 0

    def build(self):
        self.wire_sidebar()
        grid = self.w.gridHost.layout()
        for i, (key, title, sub, col) in enumerate(APPS):
            c = ClickableFrame()
            c.setProperty("card", "shadow")
            c.setFixedHeight(132)
            c.setCursor(Qt.PointingHandCursor)
            cl = QVBoxLayout(c)
            cl.setContentsMargins(0, 0, 0, 0)
            cl.setSpacing(0)
            body = QVBoxLayout()
            body.setContentsMargins(12, 8, 12, 6)
            top = QHBoxLayout()
            ic = QLabel()
            ic.setPixmap(QPixmap(icon_path(ICON_FILE[key])).scaled(42, 42, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            top.addWidget(ic)
            top.addStretch(1)
            top.addWidget(mk_label(f"{i + 1:02d}", "eyebrow"), 0, Qt.AlignTop)
            body.addLayout(top)
            body.addStretch(1)
            body.addWidget(mk_label(title, "h3"))
            body.addWidget(mk_label(sub, "small"))
            cl.addLayout(body)
            bar = QFrame()
            bar.setFixedHeight(8)
            bar.setStyleSheet(f"background:{col};border:none;")
            cl.addWidget(bar)
            c.setToolTip(f"Open {title}")
            c.clicked.connect(lambda i=i: self.navigate.emit(i + 1))
            grid.addWidget(c, i // 4, i % 4)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        self.w.btnStart.clicked.connect(lambda: self.navigate.emit(1))

    def themed(self):
        pass

    def menus(self):
        return {}


class SettingsPage(SidebarPage):
    UI = "settings.ui"
    KEY = "settings"
    TITLE = "Control panel — Settings"
    PATH = "kernel98 / settings"
    NAV_INDEX = 9

    def build(self):
        self.wire_sidebar()
        w = self.w
        self.previews = []
        for btn, dark, label in ((w.btnLight, False, "Light / the classic"), (w.btnDark, True, "Dark / after hours")):
            lay = QVBoxLayout(btn)
            lay.setContentsMargins(0, 0, 0, 8)
            pv = ThemePreview(dark)
            lay.addWidget(pv, 1)
            row = QHBoxLayout()
            row.setContentsMargins(10, 0, 12, 0)
            lb = mk_label(label, "h3")
            lb.setAttribute(Qt.WA_TransparentForMouseEvents)
            dot = mk_label("○", "h3")
            dot.setAttribute(Qt.WA_TransparentForMouseEvents)
            row.addWidget(lb)
            row.addStretch(1)
            row.addWidget(dot)
            lay.addLayout(row)
            self.previews.append((btn, dot))
        w.btnLight.clicked.connect(lambda: self.prefs.update(mode="light"))
        w.btnDark.clicked.connect(lambda: self.prefs.update(mode="dark"))
        self.swatches = [getattr(w, f"acc{i}") for i in range(5)]
        for i, b in enumerate(self.swatches):
            b.setStyleSheet(f"background:{ACCENTS[i]};")
            b.clicked.connect(lambda _=False, i=i: self.prefs.update(accent=i))
        for name, key in (("tglSounds", "sounds"), ("tglMotion", "motion"), ("tglTips", "tips")):
            b = getattr(w, name)
            b.toggled.connect(lambda on, b=b, key=key: (b.setText("ON" if on else "OFF"), self.prefs.values.__setitem__(key, on)))
        w.cmbSpeed.currentIndexChanged.connect(lambda i: self.prefs.values.__setitem__("speed", i))
        w.btnRestore.clicked.connect(self.restore)
        w.btnSave.clicked.connect(self.save)
        self.sync()

    def sync(self):
        p, w = self.prefs, self.w
        dark = p["mode"] == "dark"
        w.btnLight.setChecked(not dark); w.btnDark.setChecked(dark)
        for (btn, dot), on in zip(self.previews, (not dark, dark)):
            dot.setText("●" if on else "○")
        for i, b in enumerate(self.swatches):
            b.setChecked(i == p["accent"])
        for name, key in (("tglSounds", "sounds"), ("tglMotion", "motion"), ("tglTips", "tips")):
            b = getattr(w, name)
            b.blockSignals(True); b.setChecked(p[key]); b.setText("ON" if p[key] else "OFF"); b.blockSignals(False)
        w.cmbSpeed.blockSignals(True); w.cmbSpeed.setCurrentIndex(p["speed"]); w.cmbSpeed.blockSignals(False)

    def themed(self):
        if hasattr(self, "previews"):
            self.sync()

    def restore(self):
        self.prefs.restore()
        self.sync()
        self.say("Defaults restored. Press “Save preferences” to keep them.")

    def save(self):
        self.prefs.save()
        self.say("Preferences are saved to this desktop.")

    def menus(self):
        return {}
