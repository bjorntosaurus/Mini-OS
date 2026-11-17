"""Gapscan — Fragmentation page."""
from PySide6.QtWidgets import QFrame, QHBoxLayout, QVBoxLayout

from algorithms.fragmentation import allocate
from gui.pages.base import BasePage, safe
from gui.widgets.charts import SplitBar
from gui.widgets.common import apply_shadows, clear_layout, mk_label
from utils.validators import ValidationError, parse_int_list

STRAT = {"First fit": "first", "Best fit": "best", "Worst fit": "worst", "Next fit": "next"}
MODES = {"Fixed partitions": "fixed", "Dynamic partitions": "dynamic"}


def bname(i):
    return chr(65 + i) if i < 26 else f"B{i}"


class FragmentationPage(BasePage):
    UI = "fragmentation.ui"
    KEY = "frag"
    TITLE = "Gapscan — Fragmentation"
    PATH = "kernel98 / fragmentation"
    ICON = "fragmentation"

    def build(self):
        self.blocks, self.procs = [], []
        self.strategy, self.mode, self.view, self.res = "first", "fixed", "internal", None
        self.effbar = SplitBar()
        self.w.effBarHost.layout().addWidget(self.effbar)
        self.w.btnInternal.clicked.connect(lambda: self.set_view("internal"))
        self.w.btnExternal.clicked.connect(lambda: self.set_view("external"))
        self.w.btnSetup.clicked.connect(self.setup)
        self.w.btnExport.clicked.connect(self.export)
        self.effbar.pal = self.pal
        self.audit_no = 0
        self.recalc()

    def set_view(self, v):
        self.view = v
        self.w.btnInternal.setChecked(v == "internal")
        self.w.btnExternal.setChecked(v == "external")
        self.render()

    def recalc(self):
        if not self.blocks or not self.procs:
            self.res = None
            return self.render_empty()
        self.res = allocate(self.blocks, self.procs, self.strategy, self.mode)
        self.render()

    def render_empty(self):
        w = self.w
        w.lblBig.setText("0"); w.lblBigCap.setText("KB / " + ("INTERNAL WASTE" if self.view == "internal" else "EXTERNAL FRAGMENTATION"))
        w.lblPct.setText("no data yet"); w.lblAudit.setText("AUDIT NO. 000")
        w.lblTotal.setText("0 KB"); w.lblUsed.setText("0 KB"); w.lblExt.setText("0 KB")
        w.lblCfg.setText("NO MEMORY DEFINED")
        w.lblEffUsed.setText("—"); w.lblEffWaste.setText("—"); self.effbar.set_ratio(0)
        w.lblWhyT.setText("Nothing to scan yet")
        w.lblWhy.setText("Press “Setup ✎” and enter your memory blocks and process sizes.")
        clear_layout(w.partHost.layout())
        self.say("Empty. Use Setup to enter memory blocks and processes.")

    @safe
    def setup(self):
        inv_s = {v: k for k, v in STRAT.items()}
        inv_m = {v: k for k, v in MODES.items()}
        fields = [dict(key="blocks", label="Memory blocks (KB)", kind="multi", default=", ".join(map(str, self.blocks)), hint="e.g. 100, 500, 200"),
                  dict(key="procs", label="Process sizes (KB)", kind="multi", default=", ".join(map(str, self.procs)), hint="e.g. 212, 417, 112"),
                  dict(key="strategy", label="Allocation strategy", kind="combo", items=list(STRAT), default=inv_s[self.strategy]),
                  dict(key="mode", label="Memory model", kind="combo", items=list(MODES), default=inv_m[self.mode])]

        def parse(v):
            b = parse_int_list(v["blocks"], "Memory blocks", 1)
            p = parse_int_list(v["procs"], "Process sizes", 1)
            allocate(b, p, STRAT[v["strategy"]], MODES[v["mode"]])
            return b, p, STRAT[v["strategy"]], MODES[v["mode"]]
        r = self.ask("Setup memory", fields, parse, "Enter any number of blocks and processes, separated by commas, spaces or new lines.")
        if r:
            self.blocks, self.procs, self.strategy, self.mode = r
            self.audit_no += 1
            self.recalc()

    def render(self):
        r, w = self.res, self.w
        if r is None:
            return self.render_empty()
        fixed = r.mode == "fixed"
        total = r.total_memory
        allocated = total - r.free_total if fixed else r.used
        if self.view == "internal":
            w.lblBig.setText(f"{r.internal:,}")
            w.lblBigCap.setText("KB / INTERNAL WASTE")
            w.lblPct.setText(f"{r.internal / allocated * 100:.1f}% of allocated memory" if allocated else "no memory allocated")
        else:
            w.lblBig.setText(f"{r.external:,}")
            w.lblBigCap.setText("KB / EXTERNAL FRAGMENTATION")
            w.lblPct.setText(f"{r.external / total * 100:.1f}% of total memory")
        w.lblAudit.setText(f"AUDIT NO. {self.audit_no:03d}")
        w.lblTotal.setText(f"{total:,} KB"); w.lblUsed.setText(f"{r.used:,} KB"); w.lblExt.setText(f"{r.external:,} KB")
        w.lblCfg.setText(f"{len(self.blocks)} blocks / {r.mode.upper()} / {r.strategy.upper()} FIT")
        waste = total - r.used
        w.lblEffUsed.setText(f"{r.used / total * 100:.1f}% used")
        w.lblEffWaste.setText(f"{waste / total * 100:.1f}% {'wasted' if fixed else 'free'}")
        self.effbar.set_ratio(r.used / total)
        if r.external:
            who = ", ".join(f"P{i + 1} ({self.procs[i]} KB)" for i in r.unallocated)
            w.lblWhy.setText(f"{r.free_total:,} KB is free but split into pieces (largest {r.largest_free:,} KB). {who} cannot fit. Compaction would merge the holes.")
            w.lblWhyT.setText("Why compact?")
        elif r.unallocated:
            w.lblWhyT.setText("Not enough memory")
            w.lblWhy.setText("Unplaced: " + ", ".join(f"P{i + 1} ({self.procs[i]} KB)" for i in r.unallocated) + ". Even all free memory would be too small.")
        elif r.internal:
            w.lblWhyT.setText("Why not compact?")
            w.lblWhy.setText("These gaps are inside allocated partitions. Moving partitions will not reclaim them.")
        else:
            w.lblWhyT.setText("No waste found")
            w.lblWhy.setText("Every allocated byte is used and nothing is stranded.")
        self._cards()
        self.say(f"{r.mode.capitalize()} partitions / {total:,} KB / {r.internal:,} KB internal waste / {r.external:,} KB external / Audit complete")

    def _cards(self):
        r, lay = self.res, self.w.partHost.layout()
        clear_layout(lay)
        fixed = r.mode == "fixed"
        items = []
        if self.view == "internal":
            for b in r.blocks:
                items.append(("PARTITION " + bname(b.index), b.size, b.used, b.internal if fixed else b.free, b.processes, b.free))
        else:
            for b in r.blocks:
                if b.free:
                    items.append(("HOLE " + bname(b.index), b.size, b.size - b.free, b.free, b.processes, b.free))
        col = 0
        k = 0
        for title, size, used, waste, procs, free in items:
            f = QFrame()
            f.setProperty("card", "shadow")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(16, 10, 16, 10)
            fl.setSpacing(6)
            top = QHBoxLayout()
            top.addWidget(mk_label(title, "eyebrow"))
            top.addStretch(1)
            top.addWidget(mk_label(f"{size:,} KB", "eyebrow"))
            fl.addLayout(top)
            who = ", ".join(f"P{i + 1}" for i in procs)
            fl.addWidget(mk_label(f"{used:,} KB used" + (f"  ({who})" if who else "") if used or procs else "Free", "h2"))
            bar = SplitBar()
            bar.pal = self.pal
            bar.set_ratio(used / size)
            fl.addWidget(bar)
            lab = QHBoxLayout()
            lab.addWidget(mk_label(f"● {used:,} KB occupied", "eyebrow"))
            lab.addStretch(1)
            lab.addWidget(mk_label(f"{waste:,} KB " + ("wasted" if fixed and self.view == "internal" else "free"), "eyebrow"))
            fl.addLayout(lab)
            lay.addWidget(f, k // 2, k % 2)
            k += 1
        if self.view == "external":
            for i in r.unallocated:
                f = QFrame()
                f.setProperty("card", "plain")
                fl = QVBoxLayout(f)
                fl.setContentsMargins(16, 10, 16, 10)
                fl.addWidget(mk_label(f"UNALLOCATED / P{i + 1}", "eyebrow"))
                fl.addWidget(mk_label(f"{self.procs[i]:,} KB waiting", "h2"))
                fl.addWidget(mk_label("No single block is large enough.", "small"))
                lay.addWidget(f, k // 2, k % 2)
                k += 1
            if k == 0:
                lay.addWidget(mk_label("No free holes and no unallocated processes: no external fragmentation.", "mono", wrap=True), 0, 0, 1, 2)
        if self.view == "internal" and r.unallocated:
            for i in r.unallocated:
                f = QFrame()
                f.setProperty("card", "plain")
                fl = QVBoxLayout(f)
                fl.setContentsMargins(16, 10, 16, 10)
                fl.addWidget(mk_label(f"UNALLOCATED / P{i + 1}", "eyebrow"))
                fl.addWidget(mk_label(f"{self.procs[i]:,} KB could not be placed", "h3"))
                lay.addWidget(f, k // 2, k % 2)
                k += 1
        lay.setRowStretch(k // 2 + 1, 1)
        lay.setColumnStretch(0, 1)
        lay.setColumnStretch(1, 1)
        apply_shadows(self.w.partHost, self.pal["shadow"], 4)

    def themed(self):
        if getattr(self, "res", None):
            self._cards()

    @safe
    def export(self):
        r = self.res
        if r is None:
            raise ValidationError("Nothing to export yet. Use Setup to enter memory blocks and processes.")
        path = self.pick_save("Export report", "fragmentation_report.txt", "Text (*.txt)")
        if not path:
            return
        lines = [f"Gapscan report — {r.mode} partitions, {r.strategy} fit", f"Total memory: {r.total_memory} KB",
                 f"Used: {r.used} KB   Internal fragmentation: {r.internal} KB   External fragmentation: {r.external} KB",
                 f"Free memory: {r.free_total} KB (largest hole {r.largest_free} KB)", ""]
        for b in r.blocks:
            lines.append(f"Block {bname(b.index)} ({b.size} KB): used {b.used}, internal {b.internal}, free {b.free}, processes "
                         + (", ".join(f"P{i + 1}" for i in b.processes) or "-"))
        lines += ["", "Unallocated: " + (", ".join(f"P{i + 1}" for i in r.unallocated) or "none")]
        open(path, "w", encoding="utf-8").write("\n".join(lines))
        self.say(f"Report saved to {path}")

    def reset(self):
        self.blocks, self.procs, self.audit_no = [], [], 0
        self.recalc()

    def menus(self):
        return {"File": [("Setup memory…", self.setup), ("Reset", self.reset)],
                "Partition audit": [("Setup memory…", self.setup)],
                "Internal waste": [("Show internal view", lambda: self.set_view("internal"))],
                "External holes": [("Show external view", lambda: self.set_view("external"))],
                "Export report": [("Save report…", self.export)]}
