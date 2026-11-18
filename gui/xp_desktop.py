"""Windows-XP-style desktop: wallpaper, desktop shortcuts, draggable XP windows, "My OS Lab" explorer, Start menu, task bar."""
import os
import time

from PySide6.QtCore import QEvent, QPoint, QRect, QSize, Qt, QTimer, QTime, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QFont, QIcon, QPainter, QPixmap
from PySide6.QtWidgets import (QApplication, QFrame, QScrollArea, QGraphicsDropShadowEffect, QGraphicsOpacityEffect, QHBoxLayout, QInputDialog, QLabel,
                               QMenu, QMessageBox, QPushButton, QSizeGrip, QVBoxLayout, QWidget)

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
from gui.widgets.common import ROOT, ClickableFrame, Names, clear_layout, icon_path, load_ui, mk_label
from gui.dialogs.wallpaper_dialog import WallpaperDialog
from gui.wallpapers import DEFAULT as WP_DEFAULT, is_image, join_library, parse_library, render as render_wallpaper
from gui.xp_theme import XP_FONT, chrome_qss, explorer_qss, menu_qss, start_qss, taskbar_qss, window_frame_qss

XP_APPS = [("Dispatch", "CPU scheduling"), ("Safehouse", "Banker’s algorithm"), ("Pageport", "Paging"), ("Framelog", "Page replacement"),
           ("Segment Studio", "Segmentation"), ("Gapscan", "Fragmentation"), ("Seek", "Disk scheduling"), ("Resident", "Multiprogramming")]
PAGE_CLASSES = [HomePage, CpuPage, BankersPage, PagingPage, PageRepPage, SegmentationPage, FragmentationPage, DiskPage, MultiPage, SettingsPage]
ICONS = [ICON_FILE[a[0]] for a in APPS]
BASE_PATH = "C:\\Kernel\\Applications"


def app_for(path):
    """'C:\\Kernel\\Applications\\Seek' / 'seek' / 'disk scheduling' -> app index 1..8 (0 = not found)."""
    last = path.replace("/", "\\").rstrip("\\").split("\\")[-1].strip().lower()
    for i, (n, s) in enumerate(XP_APPS):
        if last in (n.lower(), s.lower()):
            return i + 1
    return 0


def icon_for(idx):
    if idx == 0:
        return "xp_computer"
    if idx == 9:
        return "xp_control"
    return ICONS[idx - 1]


class Wallpaper(QWidget):
    """Desktop surface. The wallpaper is painted once into a cached pixmap (rebuilt shortly after a resize settles),
    so repainting while windows move is just one blit."""
    resized = Signal()
    cleared = Signal()
    contextRequested = Signal(QPoint)
    imagesDropped = Signal(list)

    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.spec, self.mode, self._cache = WP_DEFAULT, "Fill", None
        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self.rebuild)
        self.setAttribute(Qt.WA_OpaquePaintEvent)

    def set_source(self, spec, mode):
        self.spec, self.mode = spec, mode
        self.rebuild()

    def rebuild(self):
        if self.width() > 0:
            self._cache = render_wallpaper(self.spec, self.mode, self.size())
            self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        if self._cache is None:
            self.rebuild()
        if self._cache.size() == self.size():
            p.drawPixmap(0, 0, self._cache)
        else:                                            # mid-resize: cheap stretch until the timer rebuilds
            p.drawPixmap(self.rect(), self._cache)

    def resizeEvent(self, e):
        self._timer.start(120)
        self.resized.emit()

    def mousePressEvent(self, e):
        self.cleared.emit()

    @staticmethod
    def _image_paths(ev):
        return [u.toLocalFile() for u in ev.mimeData().urls() if u.isLocalFile() and is_image(u.toLocalFile())]

    def dragEnterEvent(self, e):
        if self._image_paths(e):
            e.acceptProposedAction()

    def dropEvent(self, e):
        paths = self._image_paths(e)
        if paths:
            self.imagesDropped.emit(paths)
            e.acceptProposedAction()

    def contextMenuEvent(self, e):
        self.contextRequested.emit(e.globalPos())


class XPWindow(QFrame):
    activated = Signal(object)
    closed = Signal(object)
    minimized = Signal(object)

    def __init__(self, parent, key, title, icon):
        super().__init__(parent)
        self.key, self.page, self.maximized, self._drag, self._normal = key, None, False, None, None
        self.setObjectName("xpWindow")
        self.setProperty("active", True)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(3, 0, 3, 3)
        self.ui = load_ui("xp_window.ui")
        lay.addWidget(self.ui)
        self.w = Names(self.ui)
        self.w.lblTitle.setText(title)
        self.w.lblIcon.setPixmap(QPixmap(icon_path(icon)).scaled(18, 18, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.w.xpTitle.installEventFilter(self)
        self.w.btnMin.clicked.connect(lambda: self.minimized.emit(self))
        self.w.btnMax.clicked.connect(self.toggle_max)
        self.w.btnClose.clicked.connect(lambda: self.closed.emit(self))
        self.grip = QSizeGrip(self)
        self.grip.setFixedSize(16, 16)
        self.setStyleSheet(window_frame_qss())
        css = chrome_qss()
        for name in ("xpTitle", "xpMenu", "xpStatus"):
            getattr(self.w, name).setStyleSheet(css)
        self.taskbtn = None

    def set_active(self, on):
        if self.property("active") == on:
            return
        for w in (self, self.w.xpTitle):
            w.setProperty("active", on)
            w.style().unpolish(w)
            w.style().polish(w)

    def set_body(self, widget):
        """Host `widget` in a scroll area: if the window is made smaller than the content needs, scroll bars appear
        instead of the content being cut off."""
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setStyleSheet("QScrollArea{background:transparent;border:none;}"
                         "QScrollBar:vertical{width:14px;background:#ece9d8;} QScrollBar:horizontal{height:14px;background:#ece9d8;}"
                         "QScrollBar::handle{background:#b9c8f0;border:1px solid #6b8bd8;min-height:30px;min-width:30px;}"
                         "QScrollBar::add-line,QScrollBar::sub-line{width:0;height:0;}")
        sa.setWidget(widget)
        self.w.bodyHost.layout().addWidget(sa)
        self.setMinimumSize(360, 240)

    def set_page(self, page):
        self.page = page
        self.set_body(page)
        page.status.connect(self.w.lblStatus.setText)
        self.build_menus(page.menus() or {})

    def build_menus(self, menus, extra=None):
        host = self.w.menuHost.layout()
        clear_layout(host)
        fileacts = list(menus.get("File", []))
        fileacts += ([None] if fileacts else []) + [("Close", lambda: self.closed.emit(self))]
        menus = {"File": fileacts, **{k: v for k, v in menus.items() if k != "File"}}
        for name, actions in menus.items():
            b = QPushButton(name)
            b.clicked.connect(lambda _=False, b=b, a=actions: self.popup(b, a))
            host.addWidget(b)

    def popup(self, btn, actions):
        m = QMenu(self)
        for a in actions:
            if a is None:
                m.addSeparator()
            else:
                act = m.addAction(a[0])
                act.triggered.connect(lambda _=False, f=a[1]: f())
        m.exec(btn.mapToGlobal(QPoint(0, btn.height())))

    def toggle_max(self):
        par = self.parentWidget()
        if not self.maximized:
            self._normal = self.geometry()
            self.setGeometry(0, 0, par.width(), par.height())
        else:
            self.setGeometry(self._normal)
        self.maximized = not self.maximized

    def refit(self):
        if self.maximized:
            self.setGeometry(0, 0, self.parentWidget().width(), self.parentWidget().height())

    def eventFilter(self, obj, ev):
        if obj is self.w.xpTitle:
            t = ev.type()
            if t == QEvent.MouseButtonPress and ev.button() == Qt.LeftButton:
                self.activated.emit(self)
                self._drag = ev.globalPosition().toPoint() - self.pos()
            elif t == QEvent.MouseMove and self._drag is not None and not self.maximized:
                p = ev.globalPosition().toPoint() - self._drag
                par = self.parentWidget()
                self.move(max(-self.width() + 120, min(p.x(), par.width() - 120)), max(0, min(p.y(), par.height() - 30)))
            elif t == QEvent.MouseButtonRelease:
                self._drag = None
            elif t == QEvent.MouseButtonDblClick:
                self.toggle_max()
        return super().eventFilter(obj, ev)

    def mousePressEvent(self, e):
        self.activated.emit(self)
        super().mousePressEvent(e)

    def resizeEvent(self, e):
        self.grip.move(self.width() - 18, self.height() - 18)
        self.grip.raise_()
        super().resizeEvent(e)


class AppTile(ClickableFrame):
    def __init__(self, idx, xpname, sub, size):
        super().__init__()
        self.idx, self.xpname, self.sub = idx, xpname, sub
        self.lay = QVBoxLayout(self)
        self.lay.setContentsMargins(6, 6, 6, 6)
        self.lay.setSpacing(2)
        self.pic = QLabel()
        self.pic.setAlignment(Qt.AlignCenter)
        self.name = mk_label(xpname)
        self.name.setAlignment(Qt.AlignCenter)
        self.name.setStyleSheet(f"font-family:{XP_FONT};font-weight:bold;font-size:12px;color:#1e3c8c;background:transparent;")
        self.subl = mk_label(sub)
        self.subl.setAlignment(Qt.AlignCenter)
        self.subl.setStyleSheet(f"font-family:{XP_FONT};font-size:11px;color:#6a6a6a;background:transparent;")
        for w in (self.pic, self.name, self.subl):
            self.lay.addWidget(w)
        self.set_size(size)
        self.setToolTip(f"{xpname} — {sub}\nDouble-click to open")
        self.set_selected(False)

    def set_size(self, size):
        self.pic.setPixmap(QPixmap(icon_path(ICONS[self.idx - 1])).scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        self.pic.setMinimumHeight(size + 6)

    def set_selected(self, on):
        self.setStyleSheet("ClickableFrame{background:#e6eefc;border:1px dotted #316ac5;}" if on else "ClickableFrame{background:transparent;border:1px solid transparent;}")

    def mousePressEvent(self, e):
        self.clicked.emit()


class XPExplorer(QWidget):
    openApp = Signal(int)
    openSpecial = Signal(str)
    status = Signal(str)

    def __init__(self):
        super().__init__()
        self.ui = load_ui("xp_explorer.ui")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.ui)
        self.w = Names(self.ui)
        self.ui.setStyleSheet(explorer_qss() + chrome_qss())
        self.tiles, self.hist, self.hpos, self.size = [], [BASE_PATH], 0, 64
        grid = self.w.gridHost.layout()
        for i, (n, s) in enumerate(XP_APPS):
            t = AppTile(i + 1, n, s, self.size)
            t.clicked.connect(lambda t=t: self.select(t))
            t.doubleClicked.connect(lambda i=i: self.open_from_tile(i + 1))
            grid.addWidget(t, i // 4, i % 4)
            self.tiles.append(t)
        for c in range(4):
            grid.setColumnStretch(c, 1)
        w = self.w
        w.edAddr.setText(BASE_PATH)
        w.btnGo.clicked.connect(self.go)
        w.edAddr.returnPressed.connect(self.go)
        w.btnBack.clicked.connect(lambda: self.move_hist(-1))
        w.btnForward.clicked.connect(lambda: self.move_hist(1))
        w.btnUp.clicked.connect(lambda: self.navigate(BASE_PATH))
        w.btnSearch.clicked.connect(self.search)
        w.btnFolders.setCheckable(True)
        w.btnFolders.setChecked(True)
        w.btnFolders.toggled.connect(self.w.xpPane.setVisible)
        w.btnViews.clicked.connect(self.views_menu)
        w.lnkRun.clicked.connect(lambda: self.openApp.emit(1))
        w.lnkWall.clicked.connect(lambda: self.openSpecial.emit("wallpaper"))
        self.w.xpTip.setVisible(get_prefs()["tips"])
        get_prefs().changed.connect(lambda: self.w.xpTip.setVisible(get_prefs()["tips"]))
        w.lnkExport.clicked.connect(lambda: self.openSpecial.emit("export"))
        w.lnkComputer.hide()                                  # My Computer was redundant with My OS Lab
        w.lnkDocs.clicked.connect(lambda: self.openSpecial.emit("documents"))
        w.lnkPanel.clicked.connect(lambda: self.openApp.emit(9))
        for b in (w.boxTasksHead, w.boxPlacesHead, w.boxDetailsHead):
            b.setCursor(Qt.ArrowCursor)

    def select(self, tile):
        for t in self.tiles:
            t.set_selected(t is tile)

    def open_from_tile(self, idx):
        self.navigate(f"{BASE_PATH}\\{XP_APPS[idx - 1][0]}")

    # --- address bar / history
    def navigate(self, path, push=True):
        self.w.edAddr.setText(path)
        if push:
            self.hist = self.hist[:self.hpos + 1] + [path]
            self.hpos = len(self.hist) - 1
        idx = app_for(path)
        if idx:
            self.openApp.emit(idx)

    def go(self):
        text = self.w.edAddr.text().strip()
        norm = text.replace("/", "\\").rstrip("\\").lower()
        if norm in (BASE_PATH.lower(), "c:\\kernel", "my os lab"):
            return self.navigate(BASE_PATH)
        idx = app_for(text)
        if not idx or not norm.startswith("c:\\kernel\\applications") and "\\" in norm:
            QMessageBox.warning(self, "My OS Lab", f"Windows cannot find '{text}'. Check the spelling and try again.")
            self.w.edAddr.setText(self.hist[self.hpos])
            return
        self.navigate(f"{BASE_PATH}\\{XP_APPS[idx - 1][0]}")

    def move_hist(self, d):
        n = self.hpos + d
        if 0 <= n < len(self.hist):
            self.hpos = n
            self.navigate(self.hist[n], push=False)

    # --- toolbar
    def search(self):
        text, ok = QInputDialog.getText(self, "Search", "Find applications named (leave empty to show all):")
        if not ok:
            return
        key = text.strip().lower()
        hits = 0
        for t in self.tiles:
            match = not key or key in t.xpname.lower() or key in t.sub.lower()
            hits += match
            eff = None if match else QGraphicsOpacityEffect(t)
            if eff:
                eff.setOpacity(0.25)
            t.setGraphicsEffect(eff)
        self.status.emit(f"Search: {hits} of 8 applications match '{text}'" if key else "8 objects")

    def views_menu(self):
        m = QMenu(self)
        for label, size in (("Large Icons", 64), ("Small Icons", 36)):
            m.addAction(label, lambda s=size: self.set_icon_size(s))
        m.exec(self.w.btnViews.mapToGlobal(QPoint(0, self.w.btnViews.height())))

    def set_icon_size(self, size):
        for t in self.tiles:
            t.set_size(size)


class StartMenu(QFrame):
    openApp = Signal(int)
    openSpecial = Signal(str)

    def __init__(self, parent):
        super().__init__(parent, Qt.Popup)
        self.setObjectName("startMenu")
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setStyleSheet(start_qss())
        self.hidden_at = 0.0
        self.setFixedSize(430, 500)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)
        head = QFrame(); head.setObjectName("smHeader"); head.setFixedHeight(56)
        hl = QHBoxLayout(head); hl.setContentsMargins(10, 4, 10, 4)
        av = QLabel(); av.setPixmap(QPixmap(icon_path("xp_user")).scaled(44, 44, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        col = QVBoxLayout(); col.setSpacing(0)
        col.addWidget(mk_label("Student", "smname")); col.addWidget(mk_label("Local account", "smsub"))
        hl.addWidget(av); hl.addLayout(col); hl.addStretch(1)
        outer.addWidget(head)
        body = QHBoxLayout(); body.setSpacing(0); body.setContentsMargins(0, 0, 0, 0)
        left = QFrame(); left.setObjectName("smLeft")
        ll = QVBoxLayout(left); ll.setContentsMargins(4, 6, 4, 6); ll.setSpacing(0)
        ll.addWidget(mk_label("Your applications", "smhead"))
        for i, (n, s) in enumerate(XP_APPS):
            b = QPushButton(f"  {n}\n  {s}")
            b.setProperty("role", "smitem")
            b.setIcon(QIcon(icon_path(ICONS[i]))); b.setIconSize(QSize(30, 30))
            b.setToolTip(f"Open {n}")
            b.clicked.connect(lambda _=False, i=i: self._open(i + 1))
            ll.addWidget(b)
        ll.addStretch(1)
        allp = QPushButton("All Programs  →"); allp.setProperty("role", "small")
        allp.clicked.connect(lambda: self.all_programs(allp))
        ll.addWidget(allp)
        right = QFrame(); right.setObjectName("smRight"); right.setFixedWidth(190)
        rl = QVBoxLayout(right); rl.setContentsMargins(4, 8, 4, 8); rl.setSpacing(2)
        for text, ico, fn in (("My OS Lab", "xp_folder", lambda: self._special("explorer")), ("My Documents", "xp_folder", lambda: self._special("documents")),
                              ("Control Panel", "xp_control", lambda: self._open(9))):
            b = QPushButton("  " + text); b.setProperty("role", "smright"); b.setIcon(QIcon(icon_path(ico))); b.setIconSize(QSize(30, 30))
            b.clicked.connect(lambda _=False, f=fn: f()); rl.addWidget(b)
        rl.addSpacing(10)
        for text, key in (("Help and Support", "help"), ("Search", "search"), ("Run…", "run")):
            b = QPushButton("  " + text); b.setProperty("role", "smright"); b.clicked.connect(lambda _=False, k=key: self._special(k)); rl.addWidget(b)
        rl.addStretch(1)
        body.addWidget(left, 1); body.addWidget(right)
        outer.addLayout(body, 1)
        foot = QFrame(); foot.setObjectName("smFooter"); foot.setFixedHeight(40)
        fl = QHBoxLayout(foot); fl.setContentsMargins(8, 0, 12, 0)
        fl.addStretch(1)
        for text, key in (("⇥  Log off", "logoff"), ("⏻  Turn off", "turnoff")):
            b = QPushButton(text); b.setProperty("role", "smfoot"); b.clicked.connect(lambda _=False, k=key: self._special(k)); fl.addWidget(b)
        outer.addWidget(foot)

    def hideEvent(self, e):
        self.hidden_at = time.monotonic()
        super().hideEvent(e)

    def _open(self, i):
        self.hide(); self.openApp.emit(i)

    def _special(self, k):
        self.hide(); self.openSpecial.emit(k)

    def all_programs(self, btn):
        m = QMenu(self)
        m.setStyleSheet(menu_qss())
        m.addAction("Kernel / 98 desktop", lambda: (self.hide(), self.openSpecial.emit("skin98")))
        m.addSeparator()
        m.addAction("My OS Lab", lambda: self._special("explorer"))
        for i, (n, s) in enumerate(XP_APPS):
            m.addAction(f"{n} — {s}", lambda i=i: self._open(i + 1))
        m.exec(btn.mapToGlobal(QPoint(btn.width(), -m.sizeHint().height() + btn.height())))


class Shortcut(ClickableFrame):
    """Desktop icon: click selects, double-click opens, drag moves (snaps to the icon grid)."""
    dropped = Signal(object)

    def __init__(self, parent, icon, text, tip, is_shortcut, on_open, on_select):
        super().__init__(parent)
        self.setFixedSize(92, 94)
        self._press = self._origin = None
        self._dragging = False
        lay = QVBoxLayout(self)
        lay.setContentsMargins(2, 2, 2, 2); lay.setSpacing(2)
        pic = QLabel(); pic.setAlignment(Qt.AlignCenter); pic.setFixedHeight(50)
        pic.setPixmap(QPixmap(icon_path(icon)).scaled(46, 46, Qt.KeepAspectRatio, Qt.SmoothTransformation))
        if is_shortcut:                                   # little shortcut arrow, like on a real desktop
            ar = QLabel("↗", pic)
            ar.setFixedSize(13, 13); ar.setAlignment(Qt.AlignCenter)
            ar.setStyleSheet("background:white;color:#1a3a9a;border:1px solid #1a3a9a;font-size:9px;font-weight:bold;")
            ar.move(22, 36)
        self.lbl = QLabel(text); self.lbl.setAlignment(Qt.AlignHCenter | Qt.AlignTop); self.lbl.setWordWrap(True)
        eff = QGraphicsDropShadowEffect(self.lbl); eff.setBlurRadius(2); eff.setOffset(1, 1); eff.setColor(Qt.black)
        self.lbl.setGraphicsEffect(eff)
        lay.addWidget(pic); lay.addWidget(self.lbl)
        self.set_selected(False)
        self.on_open, self.on_select = on_open, on_select
        self.setToolTip(tip)

    def set_selected(self, on):
        self.lbl.setStyleSheet(f"color:white;font-family:{XP_FONT};font-size:11px;background:{'#316ac5' if on else 'transparent'};")

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.on_select(self)
            self._press, self._origin, self._dragging = e.globalPosition().toPoint(), self.pos(), False
            self.raise_()

    def mouseMoveEvent(self, e):
        if self._press is None:
            return
        d = e.globalPosition().toPoint() - self._press
        if self._dragging or d.manhattanLength() > 8:
            self._dragging = True
            par = self.parentWidget()
            p = self._origin + d
            self.move(max(0, min(p.x(), par.width() - self.width())), max(0, min(p.y(), par.height() - self.height())))

    def mouseReleaseEvent(self, e):
        if self._dragging:
            self.dropped.emit(self)
        self._press, self._dragging = None, False

    def mouseDoubleClickEvent(self, e):
        self.on_open()

    def contextMenuEvent(self, e):
        self.on_select(self)
        m = QMenu(self)
        m.setStyleSheet(menu_qss())
        m.addAction("Open", self.on_open)
        m.exec(e.globalPos())


class XPDesktop(QWidget):
    skinRequested = Signal(str)
    CELL_W, CELL_H, MARGIN = 96, 100, 8

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kernel XP — Operating System Simulator")
        self.prefs = get_prefs()
        self.ui = load_ui("xp_desktop.ui")
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.ui)
        self.w = Names(self.ui)
        self.w.xpTaskbar.setStyleSheet(taskbar_qss())          # scoped: never cascades into the simulators
        self.wall = Wallpaper()
        self.w.deskHost.layout().addWidget(self.wall)
        self.pages, self.windows, self.order, self.cascade = {}, {}, [], 0
        self.wall.set_source(self.prefs["wallpaper"], self.prefs["wp_mode"])
        self.wall.resized.connect(self.on_resize)
        self.wall.cleared.connect(lambda: self.select_shortcut(None))
        self.wall.contextRequested.connect(self.desktop_menu)
        self.wall.imagesDropped.connect(self.use_dropped_images)
        self._make_shortcuts()
        self._make_logo()
        self.start = StartMenu(self)
        self.start.openApp.connect(self.open_app)
        self.start.openSpecial.connect(self.special)
        w = self.w
        w.btnStartXP.setIcon(QIcon(icon_path("xp_computer")))
        w.btnStartXP.setIconSize(QSize(26, 26))
        w.btnStartXP.clicked.connect(self.toggle_start)
        w.btnQL1.setIcon(QIcon(icon_path("xp_folder"))); w.btnQL1.setIconSize(QSize(24, 24)); w.btnQL1.clicked.connect(lambda: self.special("explorer"))
        w.btnQL2.setIcon(QIcon(icon_path("xp_control"))); w.btnQL2.setIconSize(QSize(24, 24)); w.btnQL2.clicked.connect(lambda: self.open_app(9))
        w.btnQL1.setToolTip("My OS Lab"); w.btnQL2.setToolTip("Control Panel")
        self.clock = QTimer(self)
        self.clock.timeout.connect(self.tick)
        self.clock.start(5000)
        self.tick()
        self.prefs.changed.connect(self.apply_theme)
        QTimer.singleShot(0, lambda: self.special("explorer"))

    # ---------------------------------------------------------------- desktop icons
    def _make_shortcuts(self):
        self.shortcuts, self.cells, self._moved = [], {}, False
        specs = [("xp_folder", "My OS Lab", "My OS Lab — folder of applications", False, lambda: self.special("explorer"))]
        for i, (name, sub) in enumerate(XP_APPS):
            specs.append((ICONS[i], name, f"{name} — {sub}\nDouble-click to open", True, lambda i=i: self.open_app(i + 1)))
        for ic, tx, tip, is_sc, fn in specs:
            sc = Shortcut(self.wall, ic, tx, tip, is_sc, fn, self.select_shortcut)
            sc.dropped.connect(self.drop_shortcut)
            self.shortcuts.append(sc)
            sc.show()
        self.arrange()

    def rows(self):
        return max(1, (self.wall.height() - self.MARGIN) // self.CELL_H)

    def cell_pos(self, cell):
        c, r = cell
        return QPoint(self.MARGIN + c * self.CELL_W, self.MARGIN + r * self.CELL_H)

    def arrange(self, user=False):
        if user:
            self._moved = False
        rows = self.rows()
        for i, sc in enumerate(self.shortcuts):
            self.cells[sc] = (i // rows, i % rows)
            sc.move(self.cell_pos(self.cells[sc]))

    def drop_shortcut(self, sc):
        rows = self.rows()
        c = max(0, round((sc.x() - self.MARGIN) / self.CELL_W))
        r = max(0, min(rows - 1, round((sc.y() - self.MARGIN) / self.CELL_H)))
        c = min(c, max(0, (self.wall.width() - self.MARGIN) // self.CELL_W - 1))
        old = self.cells[sc]
        other = next((o for o, cell in self.cells.items() if cell == (c, r) and o is not sc), None)
        if other is not None:
            self.cells[other] = old
            other.move(self.cell_pos(old))
        self.cells[sc] = (c, r)
        self._moved = True
        sc.move(self.cell_pos((c, r)))

    def select_shortcut(self, s):
        for x in self.shortcuts:
            x.set_selected(x is s)

    def desktop_menu(self, gpos):
        m = QMenu(self)
        m.setStyleSheet(menu_qss())
        m.addAction("Change Wallpaper…  (use your own picture)", lambda: self.special("wallpaper"))
        m.addAction("Arrange Icons", lambda: self.arrange(True))
        m.addAction("Refresh", self.wall.rebuild)
        m.addSeparator()
        m.addAction("Properties", lambda: self.special("wallpaper"))
        m.exec(gpos)

    def _make_logo(self):
        self.logo = QLabel(self.wall)
        self.logo.setText("<span style='font-size:44px;font-weight:bold;color:white;'>kernel</span><sup style='font-size:20px;color:#ffd36b;'> xp</sup>"
                          "<br><span style='font-size:11px;color:white;'>Home edition / OS learning, the old-school way.</span>")
        self.logo.setAlignment(Qt.AlignRight)
        self.logo.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.logo.setStyleSheet(f"font-family:{XP_FONT};background:transparent;")
        eff = QGraphicsDropShadowEffect(self.logo); eff.setBlurRadius(6); eff.setOffset(1, 2); eff.setColor(Qt.black)
        self.logo.setGraphicsEffect(eff)
        self.logo.adjustSize()
        self.logo.show()

    def on_resize(self):
        W, H = self.wall.width(), self.wall.height()
        self.logo.adjustSize()
        self.logo.move(W - self.logo.width() - 28, H - self.logo.height() - 24)
        rows = self.rows()
        if not self._moved or any(r >= rows for _c, r in self.cells.values()):
            self.arrange()
        for win in self.windows.values():
            win.refit()

    def set_wallpaper(self, spec, mode):
        self.wall.set_source(spec, mode)

    def store_wallpaper(self, spec, mode, library=None):
        self.prefs.values["wallpaper"], self.prefs.values["wp_mode"] = spec, mode
        if library is not None:
            self.prefs.values["wp_library"] = join_library(library)
        self.prefs.save()
        self.set_wallpaper(spec, mode)

    def use_dropped_images(self, paths):
        """Dragging picture file(s) onto the desktop makes the last one the wallpaper and remembers all of them."""
        lib = parse_library(self.prefs["wp_library"])
        lib += [p for p in paths if p not in lib]
        self.store_wallpaper("file:" + paths[-1], "Fill", lib)

    def apply_theme(self):
        for p in self.pages.values():
            p.apply_theme()

    # ---------------------------------------------------------------- windows
    def ensure_page(self, idx):
        if idx not in self.pages:
            p = PAGE_CLASSES[idx](self.prefs)
            if hasattr(p, "navigate"):
                p.navigate.connect(self.open_app)
            self.pages[idx] = p
        return self.pages[idx]

    def open_app(self, idx):
        if idx == 0:                                          # old "My Computer" entry points now lead to My OS Lab
            return self.special("explorer")
        if self.prefs["sounds"] and idx not in self.windows:
            QApplication.beep()
        win = self.windows.get(idx)
        if win is None:
            page = self.ensure_page(idx)
            win = self.make_window(idx, page.TITLE, icon_for(idx))
            win.set_page(page)
            if idx == 9:                                      # the 'My computer' sidebar entry is gone in XP
                page.w.navHome.hide()
                page.w.lblWs.hide()
            page.on_open()
            page.mark_nav() if hasattr(page, "mark_nav") else None
            W, H = self.wall.width(), self.wall.height()
            need = page.minimumSizeHint()                     # open large enough to show everything without scrolling
            w = min(W - 20, max(1124, need.width() + 12))
            h = min(H - 20, max(760, need.height() + 90))
            off = (self.cascade % 5) * 26
            self.cascade += 1
            win.setGeometry(min(110 + off, max(0, W - w)), min(18 + off, max(0, H - h)), w, h)
        self.show_window(win)

    def make_window(self, key, title, icon):
        win = XPWindow(self.wall, key, title, icon)
        win.activated.connect(self.activate)
        win.closed.connect(self.close_window)
        win.minimized.connect(self.minimize)
        btn = QPushButton(title.split(" — ")[0])
        btn.setIcon(QIcon(icon_path(icon)))
        btn.setCheckable(True)
        btn.clicked.connect(lambda _=False, w=win: self.task_clicked(w))
        self.w.taskButtons.layout().addWidget(btn)
        win.taskbtn = btn
        self.windows[key] = win
        return win

    def show_window(self, win):
        win.show()
        win.taskbtn.show()
        self.activate(win)

    def activate(self, win):
        win.raise_()
        for w in self.windows.values():
            w.set_active(w is win)
            w.taskbtn.setChecked(w is win and w.isVisible())
        self.order = [x for x in self.order if x is not win] + [win]

    def _focus_top(self):
        vis = [w for w in self.order if w.isVisible()]
        if vis:
            self.activate(vis[-1])

    def minimize(self, win):
        win.hide()
        win.taskbtn.setChecked(False)
        self._focus_top()

    def close_window(self, win):
        win.hide()
        win.taskbtn.hide()
        win.taskbtn.setChecked(False)
        self._focus_top()

    def task_clicked(self, win):
        if win.isVisible() and win.property("active"):
            self.minimize(win)
        else:
            self.show_window(win)

    # ---------------------------------------------------------------- specials
    def special(self, kind):
        if kind == "explorer":
            win = self.windows.get("explorer")
            if win is None:
                ex = XPExplorer()
                ex.openApp.connect(self.open_app)
                ex.openSpecial.connect(self.special)
                win = self.make_window("explorer", "My OS Lab", "xp_folder")
                win.explorer = ex
                ex.status.connect(win.w.lblStatus.setText)
                win.set_body(ex)
                win.w.lblStatus.setText("8 objects")
                win.w.lblStatusR.setText("My OS Lab")
                win.build_menus(self.explorer_menus(ex))
                W, H = self.wall.width(), self.wall.height()
                w, h = min(1060, W - 250), min(665, H - 100)
                win.setGeometry(min(200, max(0, W - w)), min(85, max(0, H - h)), w, h)
            self.show_window(win)
        elif kind == "wallpaper":
            dlg = WallpaperDialog(self, self.prefs["wallpaper"], self.prefs["wp_mode"], parse_library(self.prefs["wp_library"]), self.set_wallpaper)
            if dlg.exec() == WallpaperDialog.Accepted:
                spec, mode, library = dlg.result_value()
                self.store_wallpaper(spec, mode, library)
            else:
                self.set_wallpaper(self.prefs["wallpaper"], self.prefs["wp_mode"])
        elif kind == "export":
            self.ensure_page(1).export()
        elif kind == "documents":
            docs = os.path.expanduser("~/Documents")
            QDesktopServices.openUrl(QUrl.fromLocalFile(docs if os.path.isdir(docs) else os.path.expanduser("~")))
        elif kind == "help":
            QMessageBox.information(self, "Help and Support", "Double-click an application on the desktop, in My OS Lab, or use the Start menu to open a simulator.\n"
                                    "Right-click the desktop to change the wallpaper. Control Panel holds theme, speed and sound settings.")
        elif kind == "search":
            self.special("explorer")
            self.windows["explorer"].explorer.search()
        elif kind == "run":
            text, ok = QInputDialog.getText(self, "Run", "Type the name of an application (e.g. Dispatch, Seek, Paging):")
            if ok and text.strip():
                idx = app_for(text)
                if idx:
                    self.open_app(idx)
                else:
                    QMessageBox.warning(self, "Run", f"Windows cannot find '{text}'. Make sure you typed the name correctly.")
        elif kind == "logoff":
            for w in list(self.windows.values()):
                self.close_window(w)
            self.special("explorer")
        elif kind == "turnoff":
            if QMessageBox.question(self, "Turn off Kernel XP", "Do you want to turn off the computer?") == QMessageBox.Yes:
                self.window().close()
        elif kind == "skin98":
            self.skinRequested.emit("98")

    def explorer_menus(self, ex):
        return {"Edit": [("Search…", ex.search)],
                "View": [("Large Icons", lambda: ex.set_icon_size(64)), ("Small Icons", lambda: ex.set_icon_size(36)),
                         ("Folders pane", lambda: ex.w.btnFolders.toggle())],
                "Favorites": [(n, lambda i=i: self.open_app(i + 1)) for i, (n, _s) in enumerate(XP_APPS)],
                "Tools": [("Change wallpaper…", lambda: self.special("wallpaper")), ("Control Panel", lambda: self.open_app(9)), None,
                          ("Switch to Kernel / 98 desktop", lambda: self.skinRequested.emit("98"))],
                "Help": [("Help and Support", lambda: self.special("help"))]}

    # ---------------------------------------------------------------- start menu / clock
    def toggle_start(self):
        if self.start.isVisible():
            self.start.hide()
        elif time.monotonic() - self.start.hidden_at > 0.25:     # a click on "start" that just closed the popup must not reopen it
            b = self.w.btnStartXP
            g = b.mapToGlobal(QPoint(0, 0))
            self.start.move(g.x(), g.y() - self.start.height())
            self.start.show()

    def tick(self):
        t = QTime.currentTime().toString("hh:mm AP")
        if self.w.lblClock.text() != t:
            self.w.lblClock.setText(t)
