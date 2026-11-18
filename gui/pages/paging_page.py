"""Pageport — Paging page."""
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QAbstractItemView, QComboBox, QFrame, QTableWidgetItem, QVBoxLayout

from algorithms.paging import frame_map, translate, validate_config
from gui.pages.base import BasePage, safe
from gui.widgets.common import apply_shadows, clear_layout, mk_label
from PySide6.QtWidgets import QPushButton
from utils.parsers import parse_page_table
from utils.validators import ValidationError, parse_int



class PagingPage(BasePage):
    UI = "paging.ui"
    KEY = "paging"
    TITLE = "Pageport — Paging"
    PATH = "kernel98 / paging"
    ICON = "paging"

    def build(self):
        w = self.w
        self.busy = False
        self.result = None
        for s in (256, 512, 1024, 2048, 4096):
            w.cmbPage.addItem(f"{s:,} B / page")
        w.cmbPage.setCurrentIndex(2)
        t = w.tblPages
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["PAGE", "FRAME", "VALID"])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(t.horizontalHeader().ResizeMode.Stretch)
        t.setSelectionBehavior(QAbstractItemView.SelectRows)
        t.setShowGrid(False)
        t.itemChanged.connect(lambda _i: self.refresh_ram())
        w.btnTranslate.clicked.connect(self.do_translate)
        w.edAddr.returnPressed.connect(self.do_translate)
        self.btn_bulk = QPushButton("Edit as text…")
        self.btn_bulk.setProperty("role", "mini")
        self.btn_bulk.setToolTip("Fill the whole page table in one line, e.g.  3 1 5 2 -")
        self.btn_bulk.clicked.connect(self.bulk_edit)
        w.pgBtns.layout().insertWidget(2, self.btn_bulk)
        w.btnAddPage.clicked.connect(lambda: self.add_page())
        w.btnDelPage.clicked.connect(self.del_page)
        w.spinFrames.valueChanged.connect(lambda _v: self.refresh_ram())
        w.cmbPage.currentTextChanged.connect(lambda _v: self.refresh_ram())
        w.spinFrames.setValue(4)
        self.set_table([])
        self.show_empty()

    # ---------------------------------------------------------------- table
    def set_table(self, table):
        self.busy = True
        t = self.w.tblPages
        t.setRowCount(0)
        for p, (f, v) in enumerate(table):
            self._row(p, f, v)
        self.busy = False
        self.refresh_ram()

    def _row(self, p, frame, valid):
        t = self.w.tblPages
        t.insertRow(p)
        it = QTableWidgetItem(str(p))
        it.setFlags(Qt.ItemIsEnabled | Qt.ItemIsSelectable)
        t.setItem(p, 0, it)
        t.setItem(p, 1, QTableWidgetItem("" if frame is None else str(frame)))
        cb = QComboBox()
        cb.addItems(["Yes", "No"])
        cb.setCurrentIndex(0 if valid else 1)
        cb.currentIndexChanged.connect(lambda _i: self.refresh_ram())
        t.setCellWidget(p, 2, cb)
        t.setRowHeight(p, 36)

    def add_page(self):
        self._row(self.w.tblPages.rowCount(), None, False)
        self.refresh_ram()

    def del_page(self):
        t = self.w.tblPages
        if t.rowCount() <= 1:
            return self.fail("The page table needs at least one page.")
        r = t.currentRow()
        t.removeRow(r if r >= 0 else t.rowCount() - 1)
        for i in range(t.rowCount()):
            t.item(i, 0).setText(str(i))
        self.refresh_ram()

    def read_table(self):
        t = self.w.tblPages
        out = []
        for p in range(t.rowCount()):
            txt = t.item(p, 1).text().strip()
            valid = t.cellWidget(p, 2).currentIndex() == 0
            frame = None
            if txt not in ("", "—", "-"):
                frame = parse_int(txt, f"Page {p} frame", 0)
            out.append((frame, valid))
        return out

    def page_size(self):
        txt = re.sub(r"[^0-9]", "", self.w.cmbPage.currentText().split("B")[0])
        return parse_int(txt, "Page size", 1)

    # ---------------------------------------------------------------- RAM grid
    def refresh_ram(self, highlight=None):
        if self.busy:
            return
        w = self.w
        lay = w.ramHost.layout()
        clear_layout(lay)
        try:
            nf = w.spinFrames.value()
            ps = self.page_size()
            table = self.read_table()
            if table:
                validate_config(ps, nf, table)
            fm = frame_map(table, nf)
        except ValidationError as e:
            lay.addWidget(mk_label("Error: " + str(e), "mono", wrap=True), 0, 0)
            w.lblNote.setText("Error: " + str(e))
            return
        w.lblRamInfo.setText(f"{nf:,} frames × {ps:,} bytes")
        cols = 3
        for fr, pg in enumerate(fm):
            f = QFrame()
            f.setProperty("card", "accentbox" if fr == highlight else "plain")
            f.setMinimumHeight(66)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(10, 6, 10, 6)
            fl.setSpacing(0)
            fl.addWidget(mk_label(f"FRAME {fr}", "eyebrow"))
            fl.addWidget(mk_label("Free" if pg is None else f"Page {pg}", "h2"))
            addr = mk_label(f"{fr * ps}", "eyebrow")
            addr.setAlignment(Qt.AlignRight)
            fl.addWidget(addr)
            lay.addWidget(f, fr // cols, fr % cols)
        lay.setRowStretch(len(fm) // cols + 1, 1)
        w.lblNote.setText("")

    # ---------------------------------------------------------------- translate
    @safe
    def do_translate(self):
        w = self.w
        addr = parse_int(w.edAddr.text(), "Logical address", 0)
        ps, nf, table = self.page_size(), w.spinFrames.value(), self.read_table()
        r = translate(addr, ps, table, nf)
        self.result = r
        w.lblPage.setText(f"Page {r.page}")
        w.lblOffset.setText(f"Offset: {r.offset:,} bytes")
        t = w.tblPages
        if r.status == "ok":
            w.lblFrame.setText(f"Frame {r.frame}")
            w.lblEntry.setText("Page table entry: valid")
            w.lblPhys.setText(f"{r.physical:,} B")
            w.lblPhysSub.setText("Physical address")
            w.lblResTag.setText("ADDRESS RESOLVED / VALID")
            w.lblFormula.setText(f"{r.frame} × {ps:,} + {r.offset:,} = {r.physical:,}")
            w.lblFormula2.setText(f"Page = floor({addr} / {ps})      Offset = {addr} mod {ps}")
            self.say(f"Address {addr:,} resolved to {r.physical:,} / Page {r.page} / Offset {r.offset}")
        else:
            bad = r.status == "invalid"
            w.lblFrame.setText("—")
            w.lblEntry.setText("Page table entry: " + ("missing" if bad else "invalid"))
            w.lblPhys.setText("INVALID" if bad else "FAULT")
            w.lblPhysSub.setText("No physical address")
            w.lblResTag.setText("ADDRESS NOT RESOLVED / " + ("OUT OF RANGE" if bad else "PAGE FAULT"))
            w.lblFormula.setText("Invalid address" if bad else f"Page {r.page} is not resident")
            w.lblFormula2.setText(r.message)
            self.say(r.message)
        self.refresh_ram(r.frame if r.status == "ok" else None)
        if r.page is not None and r.page < t.rowCount():
            t.selectRow(r.page)
        w.lblNote.setText("" if r.status == "ok" else r.message)

    def show_empty(self):
        w = self.w
        w.lblPage.setText("Page —"); w.lblOffset.setText("Offset: —")
        w.lblFrame.setText("Frame —"); w.lblEntry.setText("Page table entry: —")
        w.lblPhys.setText("—"); w.lblPhysSub.setText("Physical address")
        w.lblResTag.setText("ADDRESS NOT TRANSLATED YET")
        w.lblFormula.setText("Enter an address and press Translate"); w.lblFormula2.setText("Add pages to the page directory first (+ Page).")

    @safe
    def bulk_edit(self):
        """Whole page table as one list: token k = frame of page k, '-' = not resident (page fault)."""
        try:
            cur = " ".join("-" if not v or f is None else str(f) for f, v in self.read_table())
        except ValidationError:
            cur = ""
        fields = [dict(key="text", label="Frame of page 0, 1, 2…", kind="multi", default=cur, height=110, hint="3 1 5 2 -")]
        r = self.ask("Edit page table as text", fields, lambda v: parse_page_table(v["text"]),
                     "One entry per page, in page order: a frame number means the page is in memory, '-' means it is not resident. "
                     "Example:  3 1 5 2 -   (page 0→frame 3, page 1→frame 1, …, page 4 not resident). 'page:frame' pairs such as 0:3 4:- also work.")
        if r is None:
            return
        frames = [f for f, v in r if v and f is not None]
        if frames and max(frames) >= self.w.spinFrames.value():
            self.w.spinFrames.setValue(max(frames) + 1)               # make sure every named frame exists
        self.set_table(r)
        self.say(f"Page table entered: {len(r)} pages")

    def reset(self):
        self.w.spinFrames.setValue(4)
        self.set_table([])
        self.w.edAddr.setText("")
        self.show_empty()
        self.say("Page table cleared. Map pages to frames, then translate an address.")

    def menus(self):
        return {"File": [("Reset", self.reset)],
                "Address translator": [("Translate address", self.do_translate)],
                "Page directory": [("Edit as text…", self.bulk_edit), ("Add page", self.add_page), ("Remove selected page", self.del_page)],
                "Physical memory": [("Refresh frame map", self.refresh_ram)],
                "Help": [("About", lambda: self.show_text("Paging", "page = address ÷ page size, offset = address mod page size.\n"
                         "Edit the page directory (frame number and Yes/No valid flag). Pages beyond the table are invalid addresses; "
                         "pages marked No cause a page fault."))]}
