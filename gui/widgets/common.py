"""UI helpers: .ui loader, named-widget access, hard shadows, flow layout, small widgets."""
import os
from PySide6.QtCore import QEvent, QObject, QPoint, QRect, QSize, Qt, Signal, QFile
from PySide6.QtGui import QColor, QFont, QPainter, QPen, QPixmap
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import (QFrame, QGraphicsDropShadowEffect, QLabel, QLayout, QSizePolicy, QVBoxLayout, QWidget)

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
UI_DIR = os.path.join(ROOT, "ui")
ICON_DIR = os.path.join(ROOT, "assets", "icons")


def icon_path(name):
    return os.path.join(ICON_DIR, name + ".png")


def load_ui(filename, parent=None):
    loader = QUiLoader()
    f = QFile(os.path.join(UI_DIR, filename))
    if not f.open(QFile.ReadOnly):
        raise FileNotFoundError(f"Cannot open UI file {filename}")
    try:
        w = loader.load(f, parent)
    finally:
        f.close()
    if w is None:
        raise RuntimeError(f"Qt Designer file {filename} could not be loaded: {loader.errorString()}")
    return w


class Names:
    """ns.btnRun  ->  the child widget/layout whose objectName is 'btnRun'."""

    def __init__(self, root):
        self._root, self._cache = root, {}

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        if name not in self._cache:
            w = self._root.findChild(QObject, name)
            if w is None:
                raise AttributeError(f"UI file has no widget named '{name}'")
            self._cache[name] = w
        return self._cache[name]


SHADOW_CARDS = ("shadow", "shadowaccent", "accentbox2", "window")


class _ShadowTracker(QObject):
    """Cheap hard shadow: a plain solid QFrame placed behind the card and kept in sync with it.
    (QGraphicsDropShadowEffect forces every card and its children to be re-rendered off-screen on each
    repaint, which was the main cause of frame drops.)"""

    def __init__(self, card, color, offset):
        super().__init__(card)
        self.card, self.offset = card, offset
        self.sh = QFrame(card.parentWidget())
        self.sh.setAttribute(Qt.WA_TransparentForMouseEvents)
        self.set_color(color)
        card.installEventFilter(self)
        card.destroyed.connect(self.sh.deleteLater)
        self.sync()

    def set_color(self, color):
        self.sh.setStyleSheet(f"background:{color};border:none;")

    def sync(self):
        c = self.card
        if c.parentWidget() is not self.sh.parentWidget():
            if c.parentWidget() is None:
                self.sh.hide()
                return
            self.sh.setParent(c.parentWidget())
        self.sh.setGeometry(c.x() + self.offset, c.y() + self.offset, c.width(), c.height())
        self.sh.setVisible(c.isVisible())
        self.sh.stackUnder(c)

    def eventFilter(self, obj, ev):
        if ev.type() in (QEvent.Move, QEvent.Resize, QEvent.Show, QEvent.Hide, QEvent.ParentChange):
            try:
                self.sync()
            except RuntimeError:          # widget already deleted
                pass
        return False


def apply_shadows(root, color, offset=5):
    for fr in root.findChildren(QFrame):
        if fr.property("card") in SHADOW_CARDS and fr.parentWidget() is not None:
            tr = getattr(fr, "_shadow_tracker", None)
            if tr is None:
                fr._shadow_tracker = _ShadowTracker(fr, color, offset)
            else:
                tr.offset = offset
                tr.set_color(color)
                tr.sync()


def clear_layout(layout):
    while layout.count():
        it = layout.takeAt(0)
        w = it.widget()
        if w is not None:
            w.setParent(None)
            w.deleteLater()
        elif it.layout() is not None:
            clear_layout(it.layout())


def mk_label(text, kind=None, parent=None, wrap=False):
    lb = QLabel(text, parent)
    if kind:
        lb.setProperty("kind", kind)
    lb.setWordWrap(wrap)
    return lb


class FlowLayout(QLayout):
    """Left-to-right layout that wraps (Qt's standard flow-layout example)."""

    def __init__(self, parent=None, spacing=10):
        super().__init__(parent)
        self._items, self._sp = [], spacing
        self.setContentsMargins(0, 0, 0, 0)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, w):
        return self._do(QRect(0, 0, w, 0), True)

    def setGeometry(self, r):
        super().setGeometry(r)
        self._do(r, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        s = QSize()
        for it in self._items:
            s = s.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return s + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _do(self, rect, test):
        x, y, lh = rect.x(), rect.y(), 0
        for it in self._items:
            w, h = it.sizeHint().width(), it.sizeHint().height()
            if x + w > rect.right() and lh > 0:
                x, y, lh = rect.x(), y + lh + self._sp, 0
            if not test:
                it.setGeometry(QRect(QPoint(x, y), it.sizeHint()))
            x += w + self._sp
            lh = max(lh, h)
        return y + lh - rect.y()


class PalWidget(QWidget):
    """Base for custom-painted widgets: holds the current page palette."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.pal = {"bg": "#fff", "surface": "#fff", "ink": "#000", "muted": "#777", "border": "#000", "accent": "#c4f06a",
                    "accent_ink": "#000", "grid": "#ddd", "soft": "#eee", "hit": "#c4f06a", "dark": "#000", "dark_ink": "#fff"}

    def set_pal(self, pal):
        self.pal = pal
        self.update()

    def c(self, k):
        return QColor(self.pal[k])

    @staticmethod
    def mono(size=9, bold=False):
        f = QFont("JetBrains Mono")
        f.setStyleHint(QFont.Monospace)
        f.setPixelSize(size)
        f.setBold(bold)
        return f

    @staticmethod
    def sans(size=12, bold=False):
        f = QFont("Inter")
        f.setPixelSize(size)
        f.setBold(bold)
        return f


class ClickableFrame(QFrame):
    clicked = Signal()
    doubleClicked = Signal()

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self.clicked.emit()
        super().mousePressEvent(e)

    def mouseDoubleClickEvent(self, e):
        self.doubleClicked.emit()
