"""Segment Studio — Segmentation page."""
from PySide6.QtWidgets import QDialog, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout

from algorithms.segmentation import gaps, translate, validate_table
from gui.pages.base import BasePage, safe
from gui.widgets.charts import MemorySpaceWidget
from gui.widgets.common import ClickableFrame, apply_shadows, clear_layout, mk_label
from models.records import Segment
from PySide6.QtWidgets import QPushButton
from utils.parsers import parse_segments
from utils.validators import ValidationError, parse_int

SEGCOL = ["#84d9e0", "#c5b3f2", "#ffa3c4", "#ffcc62", "#c4f06a", "#ff9970", "#a9b4f9", "#9be3b0"]
PERMS = ["READ / EXECUTE", "READ / WRITE", "READ ONLY", "READ / WRITE / EXECUTE"]


class SegmentationPage(BasePage):
    UI = "segmentation.ui"
    KEY = "seg"
    TITLE = "Segment Studio — Segmentation"
    PATH = "kernel98 / segmentation"
    ICON = "segmentation"

    def build(self):
        self.segs, self.sel = [], None
        self.space = MemorySpaceWidget()
        self.w.spaceHost.layout().addWidget(self.space)
        self.space.segmentClicked.connect(self.select)
        self.w.btnProbe.clicked.connect(self.probe)
        self.w.edOffset.returnPressed.connect(self.probe)
        self.w.btnAddSeg.clicked.connect(self.add_segment)
        self.btn_bulk = QPushButton("Edit as text…")
        self.btn_bulk.setProperty("role", "link")
        self.btn_bulk.setToolTip("Type or paste the whole segment table: id name base limit")
        self.btn_bulk.clicked.connect(self.bulk_edit)
        lay = self.w.explorer.layout()
        lay.insertWidget(lay.indexOf(self.w.btnAddSeg) + 1, self.btn_bulk)
        self.space.pal = self.pal
        self.set_segments([], None)

    def color(self, sid):
        ids = sorted(s.seg_id for s in self.segs)
        return SEGCOL[ids.index(sid) % len(SEGCOL)] if sid in ids else "#ccc"

    def set_segments(self, segs, select=None):
        self.segs = sorted(segs, key=lambda s: s.seg_id)
        ids = [s.seg_id for s in self.segs]
        self.sel = select if select in ids else (ids[0] if ids else None)
        self.refresh()

    def refresh(self):
        w = self.w
        lay = w.segHost.layout()
        clear_layout(lay)
        for s in self.segs:
            c = ClickableFrame()
            c.setProperty("card", "plain")
            sel = s.seg_id == self.sel
            c.setStyleSheet(f"QFrame{{background:{self.color(s.seg_id) if sel else self.pal['surface']};border:{3 if sel else 2}px solid {self.pal['border']};}}"
                            f"QLabel{{border:none;color:{'#17323a' if sel else self.pal['ink']};}}")
            cl = QVBoxLayout(c)
            cl.setContentsMargins(12, 8, 12, 8)
            cl.setSpacing(2)
            top = QHBoxLayout()
            top.addWidget(mk_label(f"{s.seg_id} / {s.name or 'Segment'}", "h2"))
            top.addStretch(1)
            x = QPushButton("×")
            x.setProperty("role", "flat")
            x.setFixedWidth(22)
            x.setStyleSheet("border:none;background:transparent;")
            x.clicked.connect(lambda _=False, i=s.seg_id: self.remove(i))
            top.addWidget(x)
            cl.addLayout(top)
            cl.addWidget(mk_label(f"BASE  {s.base:,}", "eyebrow"))
            cl.addWidget(mk_label(f"LIMIT {s.limit:,} B", "eyebrow"))
            c.clicked.connect(lambda i=s.seg_id: self.select(i))
            c.doubleClicked.connect(lambda i=s.seg_id: self.edit(i))
            c.setToolTip("Click to select, double-click to edit")
            lay.addWidget(c)
        lay.addStretch(1)
        w.cmbSeg.clear()
        w.cmbSeg.addItems([str(s.seg_id) for s in self.segs])
        if self.sel is not None:
            w.cmbSeg.setCurrentText(str(self.sel))
        end = max([s.base + s.limit for s in self.segs] + [1])
        w.lblRange.setText(f"0–{end:,} bytes / gaps shown" if self.segs else "no segments defined yet")
        self.space.set_data(self.segs, {s.seg_id: self.color(s.seg_id) for s in self.segs}, self.sel, end)
        self.fill_inspector(None)

    def themed(self):
        if hasattr(self, "segs"):
            self.refresh()

    def select(self, sid):
        self.sel = sid
        self.w.cmbSeg.setCurrentText(str(sid))
        self.refresh()
        self.say(f"Segment {sid} selected")

    # ---------------------------------------------------------------- probe
    def fill_inspector(self, r):
        w = self.w
        seg = next((s for s in self.segs if s.seg_id == self.sel), None)
        if r is not None and r.segment is not None:
            seg = r.segment
        if seg is None:
            for n in ("lblSegName", "lblBase", "lblLimit", "lblOffsetV", "lblPhys"):
                getattr(w, n).setText("—")
            w.lblPerms.setText("—")
            w.permBox.setStyleSheet("")
            w.lblVerdict.setText("No segments")
            w.lblVerdictSub.setText("Add a segment to begin")
            w.verdict.setStyleSheet("")
            w.lblPhysSub.setText("")
            return
        w.lblSegName.setText(f"{seg.seg_id} / {seg.name or 'Segment'}")
        w.lblPerms.setText(seg.perms.replace(" / ", "   /   "))
        w.permBox.setStyleSheet(f"QFrame{{background:{self.color(seg.seg_id)};border:2px solid {self.pal['border']};}}QLabel{{color:#17323a;border:none;}}")
        w.lblBase.setText(f"{seg.base:,} B")
        w.lblLimit.setText(f"{seg.limit:,} B")
        if r is None:
            w.lblOffsetV.setText("—")
            w.lblVerdict.setText("Press Probe")
            w.lblVerdictSub.setText("Enter an offset to check the bounds")
            w.lblPhys.setText("—")
            w.lblPhysSub.setText("")

    @safe
    def probe(self):
        sid = parse_int(self.w.cmbSeg.currentText(), "Segment number", 0)
        off = parse_int(self.w.edOffset.text(), "Offset")
        r = translate(self.segs, sid, off)
        w = self.w
        if r.segment is not None:
            self.sel = sid
            self.refresh()
        self.fill_inspector(r)
        ok = r.valid
        w.verdict.setStyleSheet(f"QFrame{{background:{self.pal['hit'] if ok else '#ff8a8a'};border:2px solid {self.pal['border']};}}QLabel{{color:#1d2a22;border:none;}}")
        w.lblOffsetV.setText(f"{off:,} B")
        if ok:
            w.lblVerdict.setText(f"✓  {off} < {r.segment.limit}")
            w.lblVerdictSub.setText("Offset is within bounds")
            w.lblPhys.setText(f"{r.physical:,} B")
            w.lblPhysSub.setText(f"{r.segment.base:,} + {off} = {r.physical:,}")
            self.say(f"Segment {sid} / Offset {off} / Bounds valid / Physical address {r.physical:,}")
        else:
            w.lblVerdict.setText("✗  TRAP")
            w.lblVerdictSub.setText(r.message)
            w.lblPhys.setText("—")
            w.lblPhysSub.setText("No physical address")
            self.say(r.message)

    # ---------------------------------------------------------------- editing
    def _fields(self, s=None):
        nxt = max([x.seg_id for x in self.segs] + [-1]) + 1
        return [dict(key="id", label="Segment ID", default=nxt if s is None else s.seg_id),
                dict(key="name", label="Name", default="" if s is None else s.name, hint="optional, e.g. Code"),
                dict(key="base", label="Base address", default="" if s is None else s.base),
                dict(key="limit", label="Limit (size in bytes)", default="" if s is None else s.limit),
                dict(key="perms", label="Protection", kind="combo", items=PERMS, default="READ / WRITE" if s is None else s.perms)]

    def _parse(self, v, replacing=None):
        seg = Segment(parse_int(v["id"], "Segment ID", 0), v["name"].strip(), parse_int(v["base"], "Base address", 0),
                      parse_int(v["limit"], "Limit", 1), v["perms"])
        others = [s for s in self.segs if s.seg_id != replacing]
        validate_table(others + [seg])
        return seg

    def add_segment(self):
        seg = self.ask("Add segment", self._fields(), self._parse)
        if seg:
            self.set_segments(self.segs + [seg], seg.seg_id)
            self.say(f"Segment {seg.seg_id} added")

    def edit(self, sid):
        old = next(s for s in self.segs if s.seg_id == sid)
        seg = self.ask(f"Edit segment {sid}", self._fields(old), lambda v: self._parse(v, sid))
        if seg:
            self.set_segments([s for s in self.segs if s.seg_id != sid] + [seg], seg.seg_id)

    def remove(self, sid):
        self.set_segments([s for s in self.segs if s.seg_id != sid], None)
        self.say(f"Segment {sid} removed")

    @safe
    def bulk_edit(self):
        """The whole segment table as text (prefilled with the current segments; applying replaces them)."""
        rev = {"READ ONLY": "r", "READ / WRITE": "rw", "READ / EXECUTE": "rx", "READ / WRITE / EXECUTE": "rwx"}
        cur = "\n".join(f"{s.seg_id} {s.name or '-'} {s.base} {s.limit} {rev.get(s.perms, 'rw')}" for s in self.segs).replace(" - ", " ")
        fields = [dict(key="text", label="Segments", kind="multi", default=cur, height=220)]

        def parse(v):
            segs = parse_segments(v["text"])
            validate_table(segs)
            return segs
        r = self.ask("Edit segment table as text", fields, parse,
                     "One segment per line:  id  [name]  base  limit  [r | rw | rx | rwx].  Examples:  0 Code 1000 600 rx   or just   1 2400 400.  "
                     "Segments must not overlap in physical memory.")
        if r:
            self.set_segments(r, r[0].seg_id)
            self.say(f"Segment table entered: {len(r)} segments")

    def reset(self):
        self.set_segments([], None)
        self.say("Segment table cleared. Use “+ Add segment” to define segments.")

    def table_dialog(self):
        dlg = QDialog(self)
        dlg.setWindowTitle("Segment table")
        dlg.resize(560, 320)
        lay = QVBoxLayout(dlg)
        t = QTableWidget(len(self.segs), 6)
        t.setHorizontalHeaderLabels(["SEGMENT", "NAME", "BASE", "LIMIT", "END (exclusive)", "PROTECTION"])
        for i, s in enumerate(self.segs):
            for j, v in enumerate((s.seg_id, s.name, s.base, s.limit, s.base + s.limit, s.perms)):
                t.setItem(i, j, QTableWidgetItem(str(v)))
        t.horizontalHeader().setStretchLastSection(True)
        lay.addWidget(t)
        g = ", ".join(f"[{a:,}, {b:,})" for a, b in gaps(self.segs))
        lay.addWidget(mk_label("Gaps: " + (g or "none"), "small", wrap=True))
        dlg.exec()

    def protection_dialog(self):
        self.show_text("Protection", "\n".join(f"{s.seg_id} / {s.name}: {s.perms}" for s in self.segs) or "No segments.")

    def menus(self):
        return {"File": [("Reset", self.reset)],
                "Segments": [("Add segment…", self.add_segment), ("Edit as text…", self.bulk_edit), ("Show segment table…", self.table_dialog)],
                "Address probe": [("Probe", self.probe)], "Protection": [("Show protection flags", self.protection_dialog)],
                "Help": [("About", lambda: self.show_text("Segmentation", "physical = base + offset, valid only when 0 ≤ offset < limit.\n"
                         "Segments may not overlap in physical memory. Double-click a segment to edit it."))]}
