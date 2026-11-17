"""Display-properties style wallpaper picker: built-in wallpapers, the wallpapers/ folder, and your own pictures."""
import os

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (QComboBox, QDialog, QDialogButtonBox, QFileDialog, QHBoxLayout, QLabel, QListWidget, QListWidgetItem,
                               QPushButton, QVBoxLayout)

from gui.wallpapers import BUILTIN, MODES, WALLPAPER_DIR, folder_images, is_image, render
from gui.xp_theme import menu_qss

KIND = Qt.UserRole + 1


class WallpaperDialog(QDialog):
    """`apply(spec, mode)` is called live while you browse; result_value() returns (spec, mode, library)."""

    def __init__(self, parent, spec, mode, library, apply):
        super().__init__(parent)
        self.setWindowTitle("Display Properties — Desktop")
        self.setStyleSheet("QDialog{background:#ece9d8;} QLabel,QPushButton,QComboBox,QListWidget{font-family:Tahoma,'Segoe UI',sans-serif;font-size:12px;}"
                           "QListWidget{background:white;border:1px solid #7f9db9;} QListWidget::item:selected{background:#316ac5;color:white;}" + menu_qss())
        self.apply_cb, self.spec, self.orig = apply, spec, (spec, mode)
        self.library = list(library)
        self.resize(700, 460)
        lay = QVBoxLayout(self)
        lay.addWidget(QLabel("Choose a background for your desktop — a built-in wallpaper or your own picture:"))
        row = QHBoxLayout()
        lay.addLayout(row, 1)
        left = QVBoxLayout()
        row.addLayout(left)
        self.list = QListWidget()
        self.list.setIconSize(QSize(120, 75))
        self.list.setFixedWidth(260)
        left.addWidget(self.list, 1)
        btns = QHBoxLayout()
        self.b_add = QPushButton("Add pictures…")
        self.b_add.setToolTip("Choose one or more image files from your computer")
        self.b_add.clicked.connect(self.browse)
        self.b_rem = QPushButton("Remove")
        self.b_rem.setToolTip("Remove the selected picture from this list (the file itself is not deleted)")
        self.b_rem.clicked.connect(self.remove_selected)
        self.b_dir = QPushButton("Open folder")
        self.b_dir.setToolTip("Open the wallpapers folder — anything you put there appears in the list")
        self.b_dir.clicked.connect(lambda: QDesktopServices.openUrl(QUrl.fromLocalFile(WALLPAPER_DIR)))
        for b in (self.b_add, self.b_rem, self.b_dir):
            btns.addWidget(b)
        left.addLayout(btns)
        side = QVBoxLayout()
        row.addLayout(side, 1)
        self.preview = QLabel()
        self.preview.setFixedSize(300, 188)
        self.preview.setStyleSheet("border:8px solid #4b4b4b;border-bottom-width:14px;background:#000;")
        side.addWidget(self.preview, 0, Qt.AlignHCenter)
        self.path_lbl = QLabel("")
        self.path_lbl.setWordWrap(True)
        side.addWidget(self.path_lbl)
        mrow = QHBoxLayout()
        mrow.addWidget(QLabel("Position:"))
        self.mode_box = QComboBox()
        self.mode_box.addItems(MODES)
        self.mode_box.setCurrentText(mode if mode in MODES else "Fill")
        self.mode_box.setToolTip("Fill: cover the screen · Fit: whole picture · Stretch · Center · Tile")
        self.mode_box.currentTextChanged.connect(self.changed)
        mrow.addWidget(self.mode_box, 1)
        side.addLayout(mrow)
        side.addStretch(1)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Apply)
        bb.accepted.connect(self.accept)
        bb.rejected.connect(self.cancel)
        bb.button(QDialogButtonBox.Apply).clicked.connect(lambda: self.apply_cb(self.spec, self.mode_box.currentText()))
        lay.addWidget(bb)
        self.populate()
        self.select_spec(spec)
        self.list.currentItemChanged.connect(self.pick)
        self.refresh()

    # ---------------------------------------------------------------- list
    def _add_item(self, label, spec, kind):
        it = QListWidgetItem(QIcon(render(spec, "Fill", QSize(240, 150))), label)
        it.setData(Qt.UserRole, spec)
        it.setData(KIND, kind)
        it.setToolTip(spec[5:] if spec.startswith("file:") else label)
        self.list.addItem(it)
        return it

    def populate(self):
        self.list.blockSignals(True)
        self.list.clear()
        for key, (name, _fn) in BUILTIN.items():
            self._add_item(name, f"builtin:{key}", "builtin")
        known = set()
        for path in folder_images():
            known.add(path)
            self._add_item("Folder: " + os.path.basename(path), "file:" + path, "folder")
        self.library = [p for p in self.library if p not in known and os.path.isfile(p)]
        for path in self.library:
            self._add_item(os.path.basename(path), "file:" + path, "lib")
        self.list.blockSignals(False)

    def select_spec(self, spec):
        for i in range(self.list.count()):
            if self.list.item(i).data(Qt.UserRole) == spec:
                self.list.setCurrentRow(i)
                return
        if spec.startswith("file:") and os.path.isfile(spec[5:]):      # picture from elsewhere: keep it in the list
            self.add_paths([spec[5:]])

    def add_paths(self, paths):
        paths = [p for p in paths if is_image(p) and os.path.isfile(p)]
        if not paths:
            return 0
        for p in paths:
            if p not in self.library and p not in folder_images():
                self.library.append(p)
        self.populate()
        self.select_spec("file:" + paths[-1])
        return len(paths)

    def browse(self):
        paths, _ = QFileDialog.getOpenFileNames(self, "Select pictures", "", "Images (*.png *.jpg *.jpeg *.bmp *.gif *.webp)")
        self.add_paths(paths)

    def remove_selected(self):
        it = self.list.currentItem()
        if it is None or it.data(KIND) != "lib":
            return
        path = it.data(Qt.UserRole)[5:]
        self.library = [p for p in self.library if p != path]
        self.populate()
        self.list.setCurrentRow(0)

    # ---------------------------------------------------------------- selection
    def pick(self, item, _prev=None):
        if item is not None:
            self.spec = item.data(Qt.UserRole)
            self.changed()

    def changed(self, *_):
        self.refresh()
        self.apply_cb(self.spec, self.mode_box.currentText())

    def refresh(self):
        it = self.list.currentItem()
        is_file = self.spec.startswith("file:")
        self.preview.setPixmap(render(self.spec, self.mode_box.currentText(), QSize(284, 166)))
        self.path_lbl.setText(self.spec[5:] if is_file else "")
        self.mode_box.setEnabled(is_file)
        self.b_rem.setEnabled(it is not None and it.data(KIND) == "lib")

    def cancel(self):
        self.apply_cb(*self.orig)
        self.reject()

    def result_value(self):
        return self.spec, self.mode_box.currentText(), list(self.library)
