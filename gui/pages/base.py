"""Shared base class for every simulator page."""
import functools
import inspect
import os

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFormLayout, QLabel, QLineEdit, QMessageBox,
                               QPlainTextEdit, QCheckBox, QVBoxLayout, QWidget, QSpinBox)

from gui.theme import build_qss, palette
from gui.widgets.common import Names, apply_shadows, load_ui, PalWidget
from utils.validators import ValidationError


def safe(fn):
    """Slot decorator: validation errors become friendly dialogs, nothing ever crashes the GUI."""
    nargs = len(inspect.signature(fn).parameters) - 1

    @functools.wraps(fn)
    def wrapper(self, *args):
        try:
            return fn(self, *args[:nargs])
        except ValidationError as e:
            self.fail(str(e))
        except Exception as e:                                   # pragma: no cover - last line of defence
            self.fail(f"Unexpected problem: {e}")
    return wrapper


class FormDialog(QDialog):
    """Tiny generic input dialog. fields: dict(key, label, kind=text|multi|combo|check|int, default, items, hint)."""

    def __init__(self, parent, title, fields, intro=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setMinimumWidth(520)
        lay = QVBoxLayout(self)
        if intro:
            lb = QLabel(intro)
            lb.setWordWrap(True)
            lb.setProperty("kind", "muted")
            lay.addWidget(lb)
        form = QFormLayout()
        lay.addLayout(form)
        self.w = {}
        for f in fields:
            k, kind = f["key"], f.get("kind", "text")
            if kind == "multi":
                w = QPlainTextEdit(str(f.get("default", "")))
                w.setMinimumHeight(f.get("height", 70))
                w.setStyleSheet("font-family:'JetBrains Mono',Consolas,monospace;")
            elif kind == "combo":
                w = QComboBox()
                w.addItems(f["items"])
                if f.get("default") in f["items"]:
                    w.setCurrentText(f["default"])
            elif kind == "check":
                w = QCheckBox()
                w.setChecked(bool(f.get("default")))
            else:
                w = QLineEdit(str(f.get("default", "")))
            if f.get("hint"):
                w.setToolTip(f["hint"])
                if kind in ("text",):
                    w.setPlaceholderText(f["hint"])
            self.w[k] = w
            form.addRow(f["label"], w)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.reject)
        lay.addWidget(bb)

    def values(self):
        out = {}
        for k, w in self.w.items():
            if isinstance(w, QPlainTextEdit):
                out[k] = w.toPlainText()
            elif isinstance(w, QComboBox):
                out[k] = w.currentText()
            elif isinstance(w, QCheckBox):
                out[k] = w.isChecked()
            else:
                out[k] = w.text()
        return out


class BasePage(QWidget):
    status = Signal(str)
    UI = ""
    KEY = "cpu"
    TITLE = ""
    PATH = ""
    ICON = "cpu"

    def __init__(self, prefs, parent=None):
        super().__init__(parent)
        self.prefs = prefs
        self.ui = load_ui(self.UI)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(self.ui)
        self.w = Names(self.ui)
        self.pal = palette(self.KEY, prefs["mode"], prefs.accent_override)
        self.opened = False
        self.build()
        self.apply_theme()

    # -- to be overridden ------------------------------------------------
    def build(self):
        pass

    def themed(self):
        """Called after the palette changed; push palette into custom widgets."""

    def menus(self):
        return {}

    def reset(self):
        pass

    def on_open(self):
        """Called by the shell every time the page is shown."""
        self.opened = True

    # -- helpers ---------------------------------------------------------
    def apply_theme(self):
        self.pal = palette(self.KEY, self.prefs["mode"], self.prefs.accent_override)
        self.setStyleSheet(build_qss(self.pal))
        from PySide6.QtWidgets import QTableWidget
        for t in self.ui.findChildren(QTableWidget):
            t.horizontalHeader().setDefaultAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        apply_shadows(self.ui, self.pal["shadow"])
        for w in self.ui.findChildren(PalWidget):
            w.set_pal(self.pal)
        self.themed()

    def say(self, msg):
        self.status.emit(msg)

    def fail(self, msg):
        self.status.emit("Error: " + msg)
        QMessageBox.warning(self, "Please check your input", msg)

    def ask(self, title, fields, parse, intro=None):
        """Show a FormDialog until parse(values) succeeds or the user cancels. Returns parse() result or None."""
        defaults = fields
        while True:
            dlg = FormDialog(self, title, defaults, intro)
            if dlg.exec() != QDialog.Accepted:
                return None
            vals = dlg.values()
            for f in defaults:
                f["default"] = vals[f["key"]]
            try:
                return parse(vals)
            except ValidationError as e:
                QMessageBox.warning(self, "Please check your input", str(e))

    def pick_save(self, caption, default, filt):
        from PySide6.QtWidgets import QFileDialog
        return QFileDialog.getSaveFileName(self, caption, os.path.join(os.path.expanduser("~"), default), filt)[0]

    def show_text(self, title, text):
        QMessageBox.information(self, title, text)
