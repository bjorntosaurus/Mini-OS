"""Resident — Multiprogramming page."""
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QPushButton, QScrollArea, QVBoxLayout

from algorithms.multiprogramming import cpu_utilization, simulate
from gui.pages.base import BasePage, safe
from gui.widgets.charts import CurveWidget, StateTimelineWidget
from gui.widgets.common import ClickableFrame, apply_shadows, clear_layout, mk_label
from models.records import Program
from utils.parsers import parse_programs
from utils.validators import ValidationError, parse_float, parse_int
from PySide6.QtWidgets import QWidget

COLORS = ["#84d9e0", "#c5b3f2", "#ffa3c4", "#c4f06a", "#ffcc62", "#ff9970", "#a9b4f9", "#9be3b0"]
STATE_TXT = {"R": "RUNNING", "Y": "READY", "W": "I/O WAIT", "Q": "QUEUED", "D": "COMPLETED", "-": "NOT ARRIVED"}
SUP = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


class MultiPage(BasePage):
    UI = "multiprogramming.ui"
    KEY = "multi"
    TITLE = "Resident — Multiprogramming"
    PATH = "kernel98 / multiprogramming"
    ICON = "multiprogramming"

    def build(self):
        w = self.w
        self.progs = []
        self.total_mem, self.total_res, self.seed, self.quantum = 1024, None, 1, 1
        self.n, self.p = 1, 0.5
        self.sim = None
        self.tick = None
        self.curve = CurveWidget()
        w.curveHost.layout().addWidget(self.curve)
        self.curve.nClicked.connect(self.set_n)
        self.tl = StateTimelineWidget()
        sa = QScrollArea()
        sa.setWidgetResizable(True)
        sa.setFrameShape(QFrame.NoFrame)
        sa.setWidget(self.tl)
        w.simHost.layout().addWidget(sa)
        self.tl.cellClicked.connect(lambda k: w.sliderTick.setValue(k))
        w.btnModel.clicked.connect(lambda: w.stack.setCurrentIndex(0))
        w.btnSim.clicked.connect(lambda: w.stack.setCurrentIndex(1))
        w.btnNm.clicked.connect(lambda: self.set_n(self.n - 1))
        w.btnNp.clicked.connect(lambda: self.set_n(self.n + 1))
        w.sliderP.valueChanged.connect(lambda v: self.set_p(v / 100))
        w.btnSystem.clicked.connect(self.system_dialog)
        w.btnRunSim.clicked.connect(self.run_sim)
        w.sliderTick.valueChanged.connect(self.set_tick)
        w.sliderTick.setEnabled(False)
        self.curve.pal = self.pal
        self.tl.pal = self.pal
        self.refresh_model()
        self.refresh_cards()

    # --------------------------------------------------------------- model panel
    def set_n(self, n):
        if n < 1:
            return
        self.n = n
        self.refresh_model()

    def set_p(self, p):
        self.p = p
        self.refresh_model()

    def refresh_model(self):
        w = self.w
        u = cpu_utilization(self.n, self.p)
        w.lblU.setText(f"{u * 100:.2f}%")
        w.lblN.setText(str(self.n))
        w.lblPv.setText(f"{round(self.p * 100)}%")
        w.lblP.setText(f"p = {self.p:g}")
        w.sliderP.blockSignals(True); w.sliderP.setValue(round(self.p * 100)); w.sliderP.blockSignals(False)
        w.lblModel.setText(f"U = 1 − pⁿ = 1 − {self.p:g}{str(self.n).translate(SUP)} = {u * 100:.2f}%")
        self.curve.set_data(self.p, self.n, max(8, self.n))
        self.say(f"Independent I/O model / n = {self.n} / p = {self.p:g} / Expected utilization {u * 100:.2f}%")

    # --------------------------------------------------------------- programs
    def static_states(self):
        used, res, out = 0, 0, []
        for p in self.progs:
            ok = used + p.memory <= self.total_mem and (self.total_res is None or res + p.resources <= self.total_res)
            if ok:
                used += p.memory; res += p.resources
            out.append("RESIDENT" if ok else "QUEUED")
        return out, used

    def refresh_cards(self):
        lay = self.w.cardsHost.layout()
        clear_layout(lay)
        if self.sim is not None and self.tick is not None:
            states = [STATE_TXT[s[self.tick]] for s in self.sim.states]
            used = self.sim.mem_used[self.tick]
        else:
            states, used = self.static_states()
        for i, (p, st) in enumerate(zip(self.progs, states)):
            col = COLORS[i % len(COLORS)]
            f = ClickableFrame()
            f.setProperty("card", "plain")
            f.setFixedSize(262, 112)
            f.setStyleSheet(f"QFrame{{background:{self.pal['surface']};border:2px solid {self.pal['border']};}}QLabel{{border:none;}}")
            fl = QVBoxLayout(f)
            fl.setContentsMargins(0, 0, 0, 0)
            fl.setSpacing(0)
            hd = mk_label(f"  {p.name} / {st}", "mono")
            hd.setStyleSheet(f"background:{col};color:#1d2a22;border:none;border-bottom:2px solid {self.pal['border']};padding:5px 8px;font-size:10px;")
            fl.addWidget(hd)
            body = QHBoxLayout()
            body.setContentsMargins(12, 6, 12, 4)
            left = QVBoxLayout(); left.setSpacing(0)
            left.addWidget(mk_label(f"{p.memory:,} MB", "h2"))
            left.addWidget(mk_label(f"CPU {p.cpu_time} / {p.resources} res", "eyebrow"))
            right = QVBoxLayout(); right.setSpacing(0)
            right.addWidget(mk_label("I/O wait", "eyebrow"))
            right.addWidget(mk_label(f"{p.io_wait * 100:.0f}%", "h2"))
            body.addLayout(left); body.addStretch(1); body.addLayout(right)
            fl.addLayout(body)
            bar = QFrame()
            bar.setFixedHeight(6)
            bar.setStyleSheet(f"background:{col};border:1px solid {self.pal['border']};margin:0 12px 8px 12px;")
            fl.addWidget(bar)
            f.clicked.connect(lambda i=i: self.edit_program(i))
            f.setToolTip("Click to edit this program")
            lay.addWidget(f)
        box = QWidget()
        bl = QVBoxLayout(box)
        bl.setContentsMargins(0, 0, 0, 0)
        bl.setSpacing(8)
        add = QPushButton("+ Add program")
        add.clicked.connect(self.add_program)
        bulk = QPushButton("Paste list…")
        bulk.setToolTip("Enter all programs at once: name memory cpu io% [resources] [arrival]")
        bulk.clicked.connect(self.bulk_edit)
        for b in (add, bulk):
            b.setFixedSize(124, 52)
            bl.addWidget(b)
        lay.addWidget(box)
        lay.addStretch(1)
        apply_shadows(self.w.cardsHost, self.pal["shadow"], 4)
        pct = used / self.total_mem * 100
        self.w.btnSystem.setText(f"{used:,} / {self.total_mem:,} MB\n{pct:.0f}% memory occupied")
        self.w.cardsHost.updateGeometry()

    def sync_model(self):
        if self.progs:
            self.n = len(self.progs)
            self.p = sum(p.io_wait for p in self.progs) / len(self.progs)
        self.refresh_model()

    def _fields(self, p=None):
        d = lambda k, v: v if p is None else getattr(p, k)
        return [dict(key="name", label="Name", default=f"P{len(self.progs) + 1}" if p is None else p.name),
                dict(key="mem", label="Memory (MB)", default=128 if p is None else p.memory),
                dict(key="cpu", label="CPU time needed (ticks)", default=20 if p is None else p.cpu_time),
                dict(key="io", label="I/O wait probability (%)", default=80 if p is None else round(p.io_wait * 100, 2)),
                dict(key="res", label="Resource units (devices, files…)", default=0 if p is None else p.resources),
                dict(key="arr", label="Arrival tick", default=0 if p is None else p.arrival)]

    def _parse(self, v, skip=None):
        name = v["name"].strip()
        if not name:
            raise ValidationError("The program needs a name.")
        p = Program(name, parse_int(v["mem"], "Memory", 1), parse_int(v["cpu"], "CPU time", 1),
                    parse_float(v["io"], "I/O wait", 0, 99) / 100, parse_int(v["res"], "Resource units", 0), parse_int(v["arr"], "Arrival", 0))
        others = [q for i, q in enumerate(self.progs) if i != skip]
        simulate(others + [p], self.total_mem, self.total_res, 1, 1) if len(others) < 40 else None
        if any(q.name == name for q in others):
            raise ValidationError(f"A program named '{name}' already exists.")
        return p

    def add_program(self):
        p = self.ask("Add program", self._fields(), self._parse)
        if p:
            self.progs.append(p)
            self.after_change()

    def edit_program(self, i):
        fields = self._fields(self.progs[i])
        fields.append(dict(key="del", label="Delete this program", kind="check", default=False))

        def parse(v):
            if v["del"]:
                return "del"
            return self._parse(v, i)
        r = self.ask(f"Edit {self.progs[i].name}", fields, parse)
        if r == "del":
            if len(self.progs) > 1:
                self.progs.pop(i)
            else:
                return self.fail("At least one program is required.")
        elif r:
            self.progs[i] = r
        if r:
            self.after_change()

    @safe
    def bulk_edit(self):
        """All programs as text (prefilled with the current ones; applying replaces the list)."""
        cur = "\n".join(f"{p.name} {p.memory} {p.cpu_time} {p.io_wait * 100:g} {p.resources} {p.arrival}" for p in self.progs)
        fields = [dict(key="text", label="Programs", kind="multi", default=cur, height=220)]

        def parse(v):
            progs = parse_programs(v["text"])
            if not progs:
                raise ValidationError("Enter at least one program.")
            simulate(progs, self.total_mem, self.total_res, self.seed, self.quantum) if len(progs) < 40 else None   # validates sizes
            return progs
        r = self.ask("Edit programs as text", fields, parse,
                     "One program per line:  name  memory(MB)  cpu_ticks  io_wait(%)  [resource_units]  [arrival_tick].   Example:  P1 128 25 80   "
                     "or  P2 256 10 50% 2 3.   Separate with spaces, commas or tabs.")
        if r:
            self.progs = r
            self.after_change()
            self.say(f"{len(r)} programs entered")

    def after_change(self):
        self.sim, self.tick = None, None
        self.w.sliderTick.setEnabled(False)
        self.tl.set_data([], [])
        self.w.lblSimStats.setText("")
        self.sync_model()
        self.refresh_cards()

    @safe
    def system_dialog(self):
        fields = [dict(key="mem", label="Total memory (MB)", default=self.total_mem),
                  dict(key="res", label="Total resource units", default="" if self.total_res is None else self.total_res, hint="blank = unlimited"),
                  dict(key="q", label="CPU quantum (ticks)", default=self.quantum), dict(key="seed", label="Random seed", default=self.seed)]

        def parse(v):
            mem = parse_int(v["mem"], "Total memory", 1)
            res = None if not v["res"].strip() else parse_int(v["res"], "Total resource units", 0)
            q, seed = parse_int(v["q"], "Quantum", 1), parse_int(v["seed"], "Seed")
            if self.progs:
                simulate(self.progs, mem, res, seed, q) if len(self.progs) < 40 else None
            return mem, res, q, seed
        r = self.ask("System resources", fields, parse)
        if r:
            self.total_mem, self.total_res, self.quantum, self.seed = r
            self.after_change()

    # --------------------------------------------------------------- simulation
    @safe
    def run_sim(self):
        sim = simulate(self.progs, self.total_mem, self.total_res, self.seed, self.quantum)
        self.sim = sim
        w = self.w
        w.stack.setCurrentIndex(1)
        w.btnSim.setChecked(True); w.btnModel.setChecked(False)
        self.tl.set_data([p.name for p in self.progs], sim.states)
        w.sliderTick.setEnabled(True)
        w.sliderTick.setRange(0, sim.ticks - 1)
        w.sliderTick.setValue(sim.ticks - 1)
        self.set_tick(sim.ticks - 1)
        model = cpu_utilization(sim.max_degree, sum(p.io_wait for p in self.progs) / len(self.progs))
        w.lblSimStats.setText(
            f"{sim.ticks} ticks · measured CPU utilisation {sim.cpu_utilization * 100:.1f}% (model 1−pⁿ with n={sim.max_degree}: {model * 100:.1f}%) · "
            f"avg memory use {sim.avg_memory_util * 100:.1f}% · peak {sim.peak_memory:,} MB · max {sim.max_degree} resident · avg turnaround {sim.avg_turnaround:.1f}")
        self.say(f"Simulation complete / {sim.ticks} ticks / CPU {sim.cpu_utilization * 100:.1f}% busy / seed {self.seed}")

    def set_tick(self, k):
        if self.sim is None:
            return
        self.tick = k
        self.tl.set_tick(k)
        self.w.lblTick.setText(f"tick {k} / {self.sim.ticks - 1}")
        self.refresh_cards()

    def themed(self):
        if hasattr(self, "progs"):
            self.refresh_cards()

    def reset(self):
        self.progs = []
        self.n, self.p = 1, 0.5
        self.after_change()
        self.say("Reset. Add programs with “+ Add program”.")

    def menus(self):
        return {"File": [("Reset", self.reset)],
                "Resident processes": [("Add program…", self.add_program), ("Paste list… (many programs)", self.bulk_edit)],
                "Capacity model": [("System resources…", self.system_dialog), ("Show model curve", lambda: self.w.btnModel.click())],
                "What-if planner": [("Run simulation", self.run_sim), ("Sync n and p with programs", self.sync_model)],
                "Help": [("About", lambda: self.show_text("Multiprogramming", "Left: the classic model U = 1 − pⁿ.\n"
                         "Simulation: programs are admitted while memory/resource units remain, each resident program waits on I/O with its own probability "
                         "each tick (seeded), and one ready program runs per tick (round robin). States and utilisation are computed, not drawn."))]}
