"""Seek — Disk scheduling page."""
from PySide6.QtWidgets import QTableWidgetItem

from algorithms.disk_scheduling import schedule
from gui.pages.base import BasePage, safe
from gui.widgets.charts import DiskPlotWidget
from utils.validators import ValidationError, parse_int, parse_int_list

NAMES = {"FCFS": "FCFS", "SSTF": "SSTF", "SCAN": "SCAN", "CSCAN": "C-SCAN", "LOOK": "LOOK", "CLOOK": "C-LOOK"}


class DiskPage(BasePage):
    UI = "disk_scheduling.ui"
    KEY = "disk"
    TITLE = "Seek — Disk scheduling"
    PATH = "kernel98 / disk-scheduling"
    ICON = "disk"

    def build(self):
        w = self.w
        self.algo, self.res = "FCFS", None
        self.head, self.lo, self.hi, self.direction, self.count_return = 0, 0, 199, "up", True
        self.reqs = []
        self.plot = DiskPlotWidget()
        w.plotHost.layout().addWidget(self.plot)
        t = w.tblLedger
        t.setColumnCount(3)
        t.setHorizontalHeaderLabels(["#", "CYLINDER", "SEEK"])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setSectionResizeMode(t.horizontalHeader().ResizeMode.Stretch)
        t.setShowGrid(False)
        t.setEditTriggers(t.EditTrigger.NoEditTriggers)
        for key in NAMES:
            getattr(w, "btn" + key).clicked.connect(lambda _=False, k=key: self.set_algo(k))
        w.btnTrace.clicked.connect(self.trace)
        w.btnEdit.clicked.connect(self.edit_queue)
        for key in NAMES:
            getattr(w, "btn" + key).setFixedWidth(88)
        w.btnTrace.setFixedWidth(170)
        self.plot.pal = self.pal
        self.update_side()
        self.clear_display()

    def set_algo(self, a):
        self.algo = a
        for k in NAMES:
            getattr(self.w, "btn" + k).setChecked(k == a)
        self.trace_quiet()

    def update_side(self):
        self.w.lblHead.setText(str(self.head))
        self.w.lblRange.setText(f"{self.lo}–{self.hi}")

    def trace_quiet(self):
        if not self.reqs:
            return
        try:
            self._trace()
        except ValidationError as e:
            self.say("Error: " + str(e))

    @safe
    def trace(self):
        self._trace()

    def _trace(self):
        r = schedule(self.algo, self.head, self.reqs, self.lo, self.hi, self.direction, self.count_return)
        self.res = r
        w = self.w
        name = NAMES[self.algo]
        dir_txt = "" if self.algo in ("FCFS", "SSTF") else f" / {'up' if self.direction == 'up' else 'down'}"
        w.lblPlot.setText(f"HEAD MOVEMENT / {name}{dir_txt}")
        w.lblPlotRange.setText(f"{self.head} start → {r.path[-1]} end")
        labels, n = ["S"], 0
        for kd in r.kinds[1:]:
            if kd in ("S", "JS"):
                n += 1
                labels.append(str(n))
            else:
                labels.append("•")
        self.plot.set_data(r.path, labels, self.lo, self.hi)
        t = w.tblLedger
        t.setRowCount(len(r.order))
        for i, (c, s) in enumerate(zip(r.order, r.seeks), 1):
            for j, v in enumerate((i, c, s)):
                t.setItem(i - 1, j, QTableWidgetItem(str(v)))
        w.lblMoved.setText(f"{r.total:,}")
        w.lblAvg.setText(f"{r.average:.1f}")
        w.lblServed.setText(f"{len(r.order)} / {len(self.reqs)}")
        self.update_side()
        self.say(f"{name} trace complete / {r.total:,} cylinders / {len(r.order)} requests serviced")

    @safe
    def edit_queue(self):
        fields = [dict(key="head", label="Initial head position", default=self.head),
                  dict(key="lo", label="Minimum cylinder", default=self.lo), dict(key="hi", label="Maximum cylinder", default=self.hi),
                  dict(key="dir", label="Initial direction", kind="combo", items=["Up (toward higher cylinders)", "Down (toward lower cylinders)"],
                       default="Up (toward higher cylinders)" if self.direction == "up" else "Down (toward lower cylinders)"),
                  dict(key="ret", label="Count C-SCAN / C-LOOK return jump", kind="check", default=self.count_return),
                  dict(key="reqs", label="Request queue", kind="multi", default=", ".join(map(str, self.reqs)), hint="any number of cylinders")]

        def parse(v):
            lo, hi = parse_int(v["lo"], "Minimum cylinder", 0), parse_int(v["hi"], "Maximum cylinder", 0)
            head = parse_int(v["head"], "Head position", 0)
            reqs = parse_int_list(v["reqs"], "Request queue", 0)
            d = "up" if v["dir"].startswith("Up") else "down"
            schedule(self.algo, head, reqs, lo, hi, d, v["ret"])
            return head, lo, hi, d, v["ret"], reqs
        r = self.ask("Edit request queue", fields, parse)
        if r:
            self.head, self.lo, self.hi, self.direction, self.count_return, self.reqs = r
            self._trace()

    def clear_display(self):
        self.plot.set_data([], [], self.lo, self.hi)
        self.w.tblLedger.setRowCount(0)
        for n in ("Moved", "Avg", "Served"):
            getattr(self.w, "lbl" + n).setText("—")
        self.w.lblPlotRange.setText("—")

    def reset(self):
        self.reqs, self.res = [], None
        self.clear_display()
        self.say("Request queue cleared. Use “+ Edit request queue” to enter requests.")

    def compare(self):
        lines = []
        for k, n in NAMES.items():
            r = schedule(k, self.head, self.reqs, self.lo, self.hi, self.direction, self.count_return)
            lines.append(f"{n:7s} total {r.total:6,}   avg {r.average:8.1f}")
        self.show_text("All policies", "\n".join(lines))

    def menus(self):
        return {"File": [("Reset", self.reset)],
                "Request queue": [("Edit request queue…", self.edit_queue)],
                "Route policies": [(n, lambda _=False, k=k: self.set_algo(k)) for k, n in NAMES.items()] + [None, ("Compare all policies…", self.compare)],
                "Seek ledger": [("Trace disk head", self.trace)],
                "Help": [("About", lambda: self.show_text("Disk scheduling", "SCAN/C-SCAN sweep to the disk edge; LOOK/C-LOOK stop at the last request.\n"
                         "C-SCAN and C-LOOK jump back without servicing (counted unless unchecked in the queue editor)."))]}
