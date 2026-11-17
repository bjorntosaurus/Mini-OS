"""Safehouse — Banker's algorithm page."""
import re

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QAbstractItemView, QFrame, QHBoxLayout, QLabel, QSpinBox, QTableWidgetItem, QVBoxLayout, QWidget)

from algorithms.bankers_algorithm import is_safe, request_resources
from gui.pages.base import BasePage, safe
from gui.widgets.common import FlowLayout, clear_layout, mk_label
from utils.helpers import resource_names
from utils.validators import ValidationError, parse_int



def vec(v):
    return " ".join(str(x) for x in v)


class BankersPage(BasePage):
    UI = "bankers_algorithm.ui"
    KEY = "bankers"
    TITLE = "Safehouse — Banker’s algorithm"
    PATH = "kernel98 / banker’s-algorithm"
    ICON = "bankers"

    def build(self):
        w = self.w
        self.m, self.n = 3, 5
        self.busy = False
        self.avail_spins, self.req_spins = [], []
        self.last_grant = None
        t = w.tblAudit
        t.setColumnCount(4)
        t.setHorizontalHeaderLabels(["PID", "ALLOCATED", "MAXIMUM", "NEED"])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(t.horizontalHeader().ResizeMode.Stretch)
        t.setShowGrid(False)
        t.setSelectionMode(QAbstractItemView.SingleSelection)
        t.itemChanged.connect(lambda _i: self.recompute())
        self.pathflow = QWidget()
        FlowLayout(self.pathflow, 10)
        w.pathHost.layout().addWidget(self.pathflow)
        w.btnAddProc.clicked.connect(self.add_proc)
        w.btnDelProc.clicked.connect(self.del_proc)
        w.btnAddRes.clicked.connect(self.add_res)
        w.btnDelRes.clicked.connect(self.del_res)
        w.btnCheck.clicked.connect(self.check_request)
        w.btnApply.clicked.connect(self.apply_request)
        w.btnApply.setEnabled(False)
        self.set_state([0, 0, 0], [], [])

    # ------------------------------------------------------------- state <-> widgets
    def set_state(self, avail, alloc, maxm):
        self.busy = True
        self.n, self.m = len(alloc), len(avail)
        t = self.w.tblAudit
        t.setRowCount(self.n)
        for i in range(self.n):
            it = QTableWidgetItem(f"P{i}")
            it.setFlags(Qt.ItemIsEnabled)
            t.setItem(i, 0, it)
            t.setItem(i, 1, QTableWidgetItem(vec(alloc[i])))
            t.setItem(i, 2, QTableWidgetItem(vec(maxm[i])))
            nd = QTableWidgetItem("")
            nd.setFlags(Qt.ItemIsEnabled)
            t.setItem(i, 3, nd)
            t.setRowHeight(i, 34)
        self.build_resource_cards(avail)
        self.build_request_box()
        self.busy = False
        self.recompute()

    def names(self):
        return resource_names(self.m)

    def build_resource_cards(self, avail):
        lay = self.w.resHost.layout()
        clear_layout(lay)
        self.avail_spins, self.total_lbls = [], []
        for j, nm in enumerate(self.names()):
            f = QFrame()
            f.setProperty("card", "shadow")
            f.setMinimumWidth(210)
            fl = QVBoxLayout(f)
            fl.setContentsMargins(14, 8, 14, 8)
            fl.setSpacing(0)
            fl.addWidget(mk_label(f"RESOURCE {nm}", "eyebrow"))
            row = QHBoxLayout()
            sp = QSpinBox()
            sp.setRange(0, 10 ** 9)
            sp.setValue(avail[j])
            sp.setFixedSize(70, 40)
            sp.setStyleSheet("QSpinBox{border:none;background:transparent;font-size:30px;font-weight:800;padding:0;}")
            sp.valueChanged.connect(lambda _v: self.recompute())
            lb = mk_label("available / 0 total", "eyebrow")
            row.addWidget(sp)
            row.addWidget(lb)
            row.addStretch(1)
            fl.addLayout(row)
            lay.addWidget(f)
            self.avail_spins.append(sp)
            self.total_lbls.append(lb)
        lay.addStretch(1)
        from gui.widgets.common import apply_shadows
        apply_shadows(self.w.resHost, self.pal["shadow"], 4)
        self.w.lblVec.setText(" ".join(self.names()) + " vectors")
        self.w.lblRv.setText("REQUEST VECTOR / " + " · ".join(self.names()))

    def build_request_box(self):
        lay = self.w.reqHost.layout()
        clear_layout(lay)
        self.req_spins = []
        for nm in self.names():
            col = QFrame()
            col.setProperty("card", "accentbox")
            cl = QVBoxLayout(col)
            cl.setContentsMargins(0, 4, 0, 4)
            cl.setSpacing(0)
            sp = QSpinBox()
            sp.setRange(0, 10 ** 9)
            sp.setAlignment(Qt.AlignCenter)
            sp.setStyleSheet("QSpinBox{border:none;background:transparent;font-size:26px;font-weight:700;color:#2a1b27;padding:0;}")
            sp.setMinimumWidth(48)
            cl.addWidget(sp)
            lb = mk_label(nm, "mono")
            lb.setAlignment(Qt.AlignCenter)
            lb.setStyleSheet("font-size:9px;color:#2a1b27;")
            cl.addWidget(lb)
            lay.addWidget(col)
            self.req_spins.append(sp)
        self.w.cmbProc.clear()
        self.w.cmbProc.addItems([f"P{i}  /  active process" for i in range(self.n)])

    def read_state(self):
        t = self.w.tblAudit
        alloc, maxm = [], []
        for i in range(self.n):
            alloc.append(self._cell(i, 1, "allocation"))
            maxm.append(self._cell(i, 2, "maximum"))
        return [s.value() for s in self.avail_spins], alloc, maxm

    def _cell(self, i, col, what):
        txt = self.w.tblAudit.item(i, col).text()
        parts = [p for p in re.split(r"[,\s]+", txt.strip()) if p]
        if len(parts) != self.m:
            raise ValidationError(f"P{i} {what}: expected {self.m} numbers ({' '.join(self.names())}), found {len(parts)}.")
        return [parse_int(p, f"P{i} {what}", 0) for p in parts]

    # ------------------------------------------------------------- recompute / display
    def recompute(self):
        if self.busy:
            return
        w = self.w
        self.last_grant = None
        w.btnApply.setEnabled(False)
        if self.n == 0:
            self._badge("#ece9d8" if self.pal["mode"] == "light" else "#555555")
            w.lblState.setText("NO DATA")
            w.lblStateSub.setText("add a process to begin")
            self._set_path([], None)
            w.lblWork.setText("Work: —")
            for j, lb in enumerate(self.total_lbls):
                lb.setText(f"available / {self.avail_spins[j].value()} total")
            self.say("Empty system. Use “+ Process” and enter allocation and maximum rows.")
            return
        try:
            avail, alloc, maxm = self.read_state()
            res = is_safe(avail, alloc, maxm)
        except ValidationError as e:
            self._badge("#ffcc62")
            w.lblState.setText("INVALID")
            w.lblStateSub.setText("fix the highlighted input")
            self._set_path([], None)
            w.lblWork.setText("Error: " + str(e))
            self.say("Error: " + str(e))
            return
        self.busy = True
        for i in range(self.n):
            w.tblAudit.item(i, 3).setText(vec(res.need[i]))
        for j, lb in enumerate(self.total_lbls):
            tot = avail[j] + sum(a[j] for a in alloc)
            lb.setText(f"available / {tot} total")
        self.busy = False
        k = len(res.sequence)
        if res.safe:
            self._badge("#c4f06a")
            w.lblState.setText("✓ SAFE STATE")
            w.lblStateSub.setText(f"{k} / {self.n} can finish")
            work = [tuple(avail)] + [s.work_after for s in res.steps]
            w.lblWork.setText("Work: " + " → ".join("(" + ",".join(map(str, x)) + ")" for x in work))
            self.say(f"Safe sequence found: {' → '.join('P' + str(i) for i in res.sequence)}")
        else:
            self._badge("#ff8a8a")
            w.lblState.setText("✗ UNSAFE STATE")
            w.lblStateSub.setText(f"{k} / {self.n} can finish")
            stuck = ", ".join(f"P{i}" for i in res.unfinished)
            w.lblWork.setText(f"Deadlock risk: {stuck} can never get their remaining need from Work = ({','.join(map(str, res.steps[-1].work_after if res.steps else avail))}).")
            self.say("No safe sequence exists")
        self._set_path(res.sequence, res)
        w.lblPreview.setText("The matrix shows the original resource snapshot. Check a request before committing an allocation.")

    def _badge(self, color):
        self.w.badge.setStyleSheet(f"QFrame{{background:{color};border:2px solid {self.pal['border']};}}QLabel{{color:#1d2a22;border:none;}}")

    def _set_path(self, seq, res):
        lay = self.pathflow.layout()
        clear_layout(lay)
        for idx, i in enumerate(seq):
            b = mk_label(f"P{i}", "h2")
            b.setAlignment(Qt.AlignCenter)
            b.setFixedSize(124, 52)
            b.setStyleSheet(f"background:{self.pal['surface']};color:{self.pal['ink']};border:2px solid {self.pal['border']};font-size:20px;font-weight:800;")
            lay.addWidget(b)
            if idx < len(seq) - 1:
                a = mk_label("→", "arrow")
                a.setStyleSheet(f"color:{self.pal['accent_ink']};font-size:20px;")
                lay.addWidget(a)
        if not seq:
            lay.addWidget(mk_label("No process can finish with the available resources." if res is not None else "—", "mono"))
        self.pathflow.setMinimumHeight(60)

    def themed(self):
        if hasattr(self, "pathflow"):
            self.recompute()

    # ------------------------------------------------------------- editing
    @safe
    def add_proc(self):
        avail, alloc, maxm = self._safe_state()
        alloc.append([0] * self.m)
        maxm.append([0] * self.m)
        self.set_state(avail, alloc, maxm)

    @safe
    def del_proc(self):
        avail, alloc, maxm = self._safe_state()
        if not alloc:
            raise ValidationError("There is no process to remove.")
        row = self.w.tblAudit.currentRow()
        row = row if 0 <= row < len(alloc) else len(alloc) - 1
        alloc.pop(row)
        maxm.pop(row)
        self.set_state(avail, alloc, maxm)

    @safe
    def add_res(self):
        avail, alloc, maxm = self._safe_state()
        self.set_state(avail + [0], [r + [0] for r in alloc], [r + [0] for r in maxm])

    @safe
    def del_res(self):
        avail, alloc, maxm = self._safe_state()
        if len(avail) <= 1:
            raise ValidationError("At least one resource type is required.")
        self.set_state(avail[:-1], [r[:-1] for r in alloc], [r[:-1] for r in maxm])

    def _safe_state(self):
        try:
            return self.read_state()
        except ValidationError:
            raise ValidationError("Fix the invalid cells in the table first.")

    def reset(self):
        self.set_state([0] * 3, [], [])
        self.say("Reset to an empty system (0 processes, 3 resources).")

    # ------------------------------------------------------------- request sandbox
    @safe
    def check_request(self):
        avail, alloc, maxm = self.read_state()
        pid = self.w.cmbProc.currentIndex()
        req = [s.value() for s in self.req_spins]
        r = request_resources(pid, req, avail, alloc, maxm)
        rv = f"({', '.join(map(str, req))})"
        if r.granted:
            seq = " → ".join(f"P{i}" for i in r.safety.sequence)
            self.w.lblPreview.setText(f"✓ P{pid} requests {rv}: GRANTED. Safe sequence afterwards: {seq}.")
            self.last_grant = (pid, req)
            self.w.btnApply.setEnabled(True)
        else:
            self.w.lblPreview.setText(f"✗ P{pid} requests {rv}: DENIED. {r.reason}")
            self.last_grant = None
            self.w.btnApply.setEnabled(False)
        self.say(f"Request sandbox: {'granted' if r.granted else 'denied'} / not applied")

    @safe
    def apply_request(self):
        if not self.last_grant:
            raise ValidationError("Check a request first; only granted requests can be applied.")
        pid, req = self.last_grant
        avail, alloc, maxm = self.read_state()
        avail = [a - r for a, r in zip(avail, req)]
        alloc[pid] = [a + r for a, r in zip(alloc[pid], req)]
        self.set_state(avail, alloc, maxm)
        self.say(f"Request applied to P{pid}")

    def menus(self):
        return {"File": [("Reset", self.reset)],
                "Resource vault": [("Add resource type", self.add_res), ("Remove last resource type", self.del_res)],
                "Request sandbox": [("Check this request", self.check_request), ("Apply granted request", self.apply_request)],
                "Safety audit": [("Re-run safety algorithm", self.recompute), ("Add process", self.add_proc), ("Remove selected process", self.del_proc)],
                "Help": [("About", lambda: self.show_text("Banker’s algorithm",
                         "Edit the Allocated and Maximum cells (one number per resource, separated by spaces) and the available counts.\n"
                         "Need = Maximum − Allocated. The safety algorithm repeatedly finishes any process whose Need ≤ Work.\n"
                         "The request sandbox runs the resource-request algorithm without changing the snapshot until you apply it."))]}
