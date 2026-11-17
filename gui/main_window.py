"""Kernel / 98 desktop shell: top bar, desktop icons, the application window and the task bar."""
from PySide6.QtCore import QPoint, Qt, QTime, QTimer, QSize, Signal
from PySide6.QtGui import QAction, QCursor, QIcon, QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QLabel, QMenu, QMessageBox, QPushButton, QVBoxLayout, QWidget)

from gui.pages.bankers_page import BankersPage
from gui.pages.cpu_page import CpuPage
from gui.pages.disk_page import DiskPage
from gui.pages.fragmentation_page import FragmentationPage
from gui.pages.home_settings import APPS, ICON_FILE, HomePage, SettingsPage
from gui.pages.multi_page import MultiPage
from gui.pages.pagerep_page import PageRepPage
from gui.pages.paging_page import PagingPage
from gui.pages.segmentation_page import SegmentationPage
from gui.settings import get_prefs
from gui.theme import shell_palette, shell_qss
from gui.widgets.common import ClickableFrame, Names, apply_shadows, icon_path, load_ui

DESK_LABELS = ["CPU scheduling", "Banker’s algorithm", "Paging", "Page replacement", "Segmentation", "Fragmentation",
               "Disk scheduling", "Multiprogramming", "Settings"]
DESK_ICONS = [ICON_FILE[a[0]] for a in APPS] + ["settings"]


class DesktopIcon(ClickableFrame):
    def __init__(self, icon, text, on_open):
        super().__init__()
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2)
        lay.setSpacing(4)
        self.pic = QLabel()
        self.pic.setPixmap(QPixmap(icon_path(icon)).scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.pic.setAlignment(Qt.AlignCenter)
        self.lbl = QLabel(text)
        self.lbl.setAlignment(Qt.AlignCenter)
        self.lbl.setWordWrap(True)
        lay.addWidget(self.pic)
        lay.addWidget(self.lbl)
        self.doubleClicked.connect(on_open)
        self.setToolTip("Double-click to open")
        self.setFixedHeight(78)

    def set_color(self, c):
        self.lbl.setStyleSheet(f"color:{c};font-family:'JetBrains Mono',Consolas,monospace;font-size:11px;background:transparent;")


class MainWindow(QWidget):
    skinRequested = Signal(str)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kernel / 98 — Operating System Simulator")
        self.prefs = get_prefs()
        self.ui = load_ui("main_window.ui")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.ui)
        self.w = Names(self.ui)
        self.pages = [HomePage, CpuPage, BankersPage, PagingPage, PageRepPage, SegmentationPage, FragmentationPage,
                      DiskPage, MultiPage, SettingsPage]
        self.pages = [P(self.prefs) for P in self.pages]
        self.current = 0
        self.maximized = False
        stack = self.w.stack
        for p in self.pages:
            stack.addWidget(p)
            p.status.connect(self.w.lblStatus.setText)
            if hasattr(p, "navigate"):
                p.navigate.connect(self.open_page)
        # desktop icons
        self.icons = []
        col = self.w.iconCol.layout()
        for i, (txt, ic) in enumerate(zip(DESK_LABELS, DESK_ICONS)):
            d = DesktopIcon(ic, txt, lambda i=i: self.open_page(i + 1 if i < 8 else 9, beep=True))
            col.addWidget(d)
            self.icons.append(d)
        col.addStretch(1)
        self.w.winArea.layout().setContentsMargins(0, 36, 50, 40)
        w = self.w
        w.btnClose.clicked.connect(self.close_window)
        w.btnMin.clicked.connect(self.close_window)
        w.btnMax.clicked.connect(self.toggle_max)
        w.btnTask.clicked.connect(self.task_clicked)
        w.btnStart.clicked.connect(self.start_menu)
        w.menuFile.clicked.connect(lambda: self.popup(w.menuFile, self.top_file()))
        w.menuView.clicked.connect(lambda: self.popup(w.menuView, self.top_view()))
        w.menuApps.clicked.connect(lambda: self.popup(w.menuApps, self.apps_menu()))
        w.menuHelp.clicked.connect(lambda: self.popup(w.menuHelp, self.help_menu()))
        self.prefs.changed.connect(self.apply_theme)
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.tick_clock)
        self.clock.start(1000)
        self.tick_clock()
        self.apply_theme()
        self.open_page(0)

    # ------------------------------------------------------------ theme
    def apply_theme(self):
        s = shell_palette(self.prefs["mode"])
        if self.prefs.accent_override:
            s["accent"] = self.prefs.accent_override
        self.setStyleSheet(shell_qss(s))
        apply_shadows(self.ui, s["shadow"], 8)
        for d in self.icons:
            d.set_color(s["toptext"])
        for p in self.pages:
            p.apply_theme()

    # ------------------------------------------------------------ navigation
    def open_page(self, i, beep=False):
        if beep and self.prefs["sounds"]:
            QApplication.beep()
        self.current = i
        p = self.pages[i]
        self.w.stack.setCurrentIndex(i)
        self.w.windowFrame.show()
        self.w.lblTitle.setText(p.TITLE)
        self.w.lblPath.setText(p.PATH)
        short = p.TITLE.split(" — ")[0]
        self.w.btnTask.setText("▣   " + short if i not in (0,) else "▦   Desktop")
        if i in (0, 9):
            p.NAV_INDEX = i
            p.mark_nav() if hasattr(p, "mark_nav") else None
        p.on_open()
        self.build_menubar(p)
        if i == 0:
            self.w.lblStatus.setText("Ready. Choose an app to start exploring.")
        elif i == 9:
            self.w.lblStatus.setText("Preferences are saved to this desktop.")

    def build_menubar(self, page):
        host = self.w.menuHost.layout()
        while host.count():
            it = host.takeAt(0)
            if it.widget():
                it.widget().setParent(None)
                it.widget().deleteLater()
        menus = page.menus() or self.generic_menus()
        for name, actions in menus.items():
            b = QPushButton(name)
            b.setCursor(Qt.PointingHandCursor)
            b.clicked.connect(lambda _=False, b=b, a=actions: self.popup(b, self.make_menu(a)))
            host.addWidget(b)

    def generic_menus(self):
        return {"File": [("Open My computer", lambda: self.open_page(0)), None, ("Close window", self.close_window), ("Exit", self.window().close)],
                "Edit": [("Preferences…", lambda: self.open_page(9))],
                "Simulation": [(t, lambda _=False, i=i: self.open_page(i + 1)) for i, t in enumerate(DESK_LABELS[:8])],
                "View": [("Light theme", lambda: self.prefs.update(mode="light")), ("Dark theme", lambda: self.prefs.update(mode="dark")),
                         None, ("Toggle maximize", self.toggle_max), ("Switch to Windows XP desktop", lambda: self.skinRequested.emit("xp"))],
                "Help": [("About Kernel / 98", self.about)]}

    def make_menu(self, actions):
        m = QMenu(self)
        for a in actions:
            if a is None:
                m.addSeparator()
            else:
                act = QAction(a[0], m)
                act.triggered.connect(lambda _=False, f=a[1]: f())
                m.addAction(act)
        return m

    def popup(self, btn, menu):
        menu.exec(btn.mapToGlobal(QPoint(0, btn.height() + 2)))

    def top_file(self):
        return self.make_menu([("Open My computer", lambda: self.open_page(0)), None, ("Exit", self.window().close)])

    def top_view(self):
        return self.make_menu([("Light theme", lambda: self.prefs.update(mode="light")), ("Dark theme", lambda: self.prefs.update(mode="dark")),
                               None, ("Toggle maximize", self.toggle_max), ("Switch to Windows XP desktop", lambda: self.skinRequested.emit("xp"))])

    def apps_menu(self):
        acts = [(t, lambda _=False, i=i: self.open_page(i + 1, True)) for i, t in enumerate(DESK_LABELS[:8])]
        return self.make_menu(acts + [None, ("Settings", lambda: self.open_page(9))])

    def help_menu(self):
        return self.make_menu([("About Kernel / 98", self.about)])

    def about(self):
        QMessageBox.information(self, "Kernel / 98", "Kernel / 98 — an offline Operating Systems lab.\n\nEight simulators: CPU scheduling, Banker’s algorithm, "
                                "paging, page replacement, segmentation, fragmentation, disk scheduling and multiprogramming.")

    def start_menu(self):
        m = self.apps_menu()
        m.addSeparator()
        m.addAction("Exit", self.window().close)
        b = self.w.btnStart
        m.exec(b.mapToGlobal(QPoint(0, -m.sizeHint().height())))

    # ------------------------------------------------------------ window chrome
    def close_window(self):
        self.w.windowFrame.hide()
        self.w.btnTask.setText("▦   Desktop")
        self.w.lblStatus.setText("")

    def task_clicked(self):
        if self.w.windowFrame.isVisible():
            self.close_window()
        else:
            self.open_page(self.current)

    def toggle_max(self):
        self.maximized = not self.maximized
        self.w.iconCol.setVisible(not self.maximized)
        self.w.winArea.layout().setContentsMargins((12, 8, 12, 12) if False else (0, 8 if self.maximized else 36, 8 if self.maximized else 50, 8 if self.maximized else 40))

    def tick_clock(self):
        self.w.lblClock.setText(QTime.currentTime().toString("hh:mm AP"))
