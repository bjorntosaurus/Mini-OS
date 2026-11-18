"""Dispatch — CPU scheduling page."""
import csv

from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QDialog, QFrame, QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget

from algorithms.cpu_scheduling import schedule
from gui.pages.base import BasePage, safe
from gui.theme import PCOL
from gui.widgets.charts import GanttWidget
from gui.widgets.common import clear_layout
from models.records import Process
from utils.helpers import pid_color
from utils.parsers import parse_processes
from utils.validators import ValidationError, parse_int



class ProcessRow(QFrame):
    """One card of the process rack: ID | arrival | burst | priority | remove."""

    def __init__(self, pid, arrival, burst, priority, color, on_remove, on_enter=None):
        super().__init__()
        self.setProperty("card", "plain")
        self.setFixedHeight(62)
        lay = QHBoxLayout(self)
        lay.setContentsMargins(0, 0, 6, 0)
        lay.setSpacing(6)
        self.idbox = QFrame()
        self.idbox.setFixedWidth(48)
        self.idbox.setStyleSheet(f"background:{color}; border:none; border-right:2px solid palette(text);")
        il = QVBoxLayout(self.idbox)
        il.setContentsMargins(2, 0, 2, 0)
        self.ed_pid = QLineEdit(pid)
        self.ed_pid.setProperty("kind", "pid")
        self.ed_pid.setAlignment(Qt.AlignCenter)
        self.ed_pid.setStyleSheet("color:#1d2a22;")
        il.addWidget(self.ed_pid)
        lay.addWidget(self.idbox)
        self.ed = {}
        for key, cap, val in (("arrival", "ARRIVAL", arrival), ("burst", "BURST", burst), ("priority", "PRIORITY", priority)):
            col = QVBoxLayout()
            col.setSpacing(0)
            col.setContentsMargins(0, 8, 0, 8)
            lb = QLabel(cap)
            lb.setProperty("kind", "eyebrow")
            lb.setStyleSheet("font-size:8px;")
            e = QLineEdit(str(val))
            e.setProperty("kind", "cell")
            e.setMinimumWidth(34)
            if on_enter:
                e.returnPressed.connect(lambda: on_enter(self))          # Enter = next row
            col.addWidget(lb)
            col.addWidget(e)
            w = QWidget()
            w.setLayout(col)
            lay.addWidget(w, 1)
            self.ed[key] = (e, w)
        btn = QPushButton("×")
        btn.setProperty("role", "flat")
        btn.setFixedWidth(20)
        btn.setToolTip("Remove this process")
        btn.clicked.connect(lambda: on_remove(self))
        lay.addWidget(btn)

    def set_color(self, c):
        self.idbox.setStyleSheet(f"background:{c}; border:none; border-right:2px solid #1d2a22;")

    def show_priority(self, on):
        self.ed["priority"][1].setVisible(on)

    def raw(self):
        return (self.ed_pid.text().strip(), self.ed["arrival"][0].text(), self.ed["burst"][0].text(), self.ed["priority"][0].text())


class CpuPage(BasePage):
    UI = "cpu_scheduling.ui"
    KEY = "cpu"
    TITLE = "Dispatch — CPU scheduling"
    PATH = "kernel98 / cpu-scheduling"
    ICON = "cpu"

    def build(self):
        w = self.w
        self.rows = []
        self.algo = "FCFS"
        self.result = None
        self.t = 0
        self.gantt = GanttWidget()
        w.ganttHost.layout().addWidget(self.gantt)
        w.rackContent.layout().addStretch(1)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        t = w.tblLedger
        t.setColumnCount(5)
        t.setHorizontalHeaderLabels(["PROCESS", "START", "FINISH", "WAIT", "TURNAROUND"])
        t.verticalHeader().setVisible(False)
        t.horizontalHeader().setStretchLastSection(True)
        t.horizontalHeader().setSectionResizeMode(t.horizontalHeader().ResizeMode.Stretch)
        t.setEditTriggers(t.EditTrigger.NoEditTriggers)
        t.setSelectionMode(t.SelectionMode.NoSelection)
        t.setShowGrid(False)
        for b, a in ((w.btnFCFS, "FCFS"), (w.btnSJF, "SJF"), (w.btnRR, "RR"), (w.btnPriority, "PRIORITY")):
            b.clicked.connect(lambda _=False, a=a: self.set_algo(a))
        w.btnAdd.clicked.connect(self.add_row)
        self.btn_bulk = QPushButton("Edit as text…  (paste many)")
        self.btn_bulk.setProperty("role", "mini")
        self.btn_bulk.setToolTip("Type or paste all processes at once: one per line, 'id arrival burst [priority]'.\nAlso accepts a block copied from Excel.")
        self.btn_bulk.clicked.connect(self.bulk_edit)
        lay = w.rack.layout()
        lay.insertWidget(lay.indexOf(w.btnAdd), self.btn_bulk)
        w.btnRun.clicked.connect(self.run)
        w.btnFirst.clicked.connect(self.first)
        w.btnPlay.clicked.connect(self.play)
        w.btnStep.clicked.connect(self.step)
        w.chkPreempt.toggled.connect(lambda: self.set_algo(self.algo))
        w.spinQuantum.valueChanged.connect(lambda: self._rerun_quiet())
        self.gantt.pal = self.pal
        self.set_algo("FCFS")
        self._empty_display()

    # ------------------------------------------------------------------ rows
    def add_row(self, pid=None, arrival=0, burst=1, priority=1):
        if not isinstance(pid, str):
            pid = f"P{self._next_id()}"
        row = ProcessRow(pid, arrival, burst, priority, pid_color(len(self.rows)), self.remove_row, self.row_enter)
        row.show_priority(self.algo == "PRIORITY")
        lay = self.w.rackContent.layout()
        lay.insertWidget(lay.count() - 1, row)
        self.rows.append(row)
        self._count()
        row.ed["arrival"][0].setFocus()
        row.ed["arrival"][0].selectAll()

    def row_enter(self, row):
        """Enter in a row jumps to the next row; on the last row it creates a new one (fast keyboard entry)."""
        i = self.rows.index(row)
        if i == len(self.rows) - 1:
            self.add_row(None, 0, "", 1)
        else:
            nxt = self.rows[i + 1].ed["arrival"][0]
            nxt.setFocus(); nxt.selectAll()

    @safe
    def bulk_edit(self):
        """One text box for the whole process list (prefilled with the current rows; applying replaces them)."""
        cur = "\n".join(" ".join(r.raw()) for r in self.rows)
        fields = [dict(key="text", label="Processes", kind="multi", default=cur, height=240)]
        res = self.ask("Edit processes as text", fields, lambda v: parse_processes(v["text"]),
                       "One process per line:  id  arrival  burst  [priority].  Separate with spaces, commas or tabs "
                       "(a block pasted from Excel works). Lines starting with # are ignored. Without an id, P1, P2… are generated.")
        if res is None:
            return
        self.clear_rows()
        for pid, a, b, pr in res:
            self.add_row(pid, a, b, pr if pr else 1)
        self.say(f"{len(res)} processes entered")
    def _next_id(self):
        used = {r.ed_pid.text() for r in self.rows}
        i = len(self.rows) + 1
        while f"P{i}" in used:
            i += 1
        return i

    def remove_row(self, row):
        self.rows.remove(row)
        row.setParent(None)
        row.deleteLater()
        for i, r in enumerate(self.rows):
            r.set_color(pid_color(i))
        self._count()

    def _count(self):
        n = len(self.rows)
        self.w.lblCount.setText(f"{n:02d} ready processes" if n != 1 else "01 ready process")

    def clear_rows(self):
        for r in list(self.rows):
            r.setParent(None)
            r.deleteLater()
        self.rows = []
        self._count()

    def _empty_display(self):
        self.w.lblCount.setText("00 ready processes")
        self.w.lblState.setText("●   READY")
        self.w.lblPlayback.setText("Playback 1× / 0 of 0 ms")

    def reset(self):
        self.timer.stop()
        self.clear_rows()
        self.result = None
        self.gantt.set_data([], {})
        self.w.tblLedger.setRowCount(0)
        for n in ("AvgWait", "AvgTat", "Busy", "Thru"):
            getattr(self.w, "lbl" + n).setText("—")
        self._empty_display()
        self.say("Reset. Add processes, pick an algorithm and run the queue.")

    # ------------------------------------------------------------------ algorithm choice
    def set_algo(self, a):
        self.algo = a
        w = self.w
        w.btnFCFS.setChecked(a == "FCFS"); w.btnSJF.setChecked(a == "SJF")
        w.btnRR.setChecked(a == "RR"); w.btnPriority.setChecked(a == "PRIORITY")
        w.chkPreempt.setVisible(a in ("SJF", "PRIORITY"))
        w.lblQ.setVisible(a == "RR"); w.spinQuantum.setVisible(a == "RR")
        for r in self.rows:
            r.show_priority(a == "PRIORITY")
        self.w.lblMode.setText(self._mode_text())
        self._rerun_quiet()

    def _mode_text(self):
        a, pre = self.algo, self.w.chkPreempt.isChecked()
        if a == "RR":
            return f"RR / quantum {self.w.spinQuantum.value()} / preemptive"
        if a == "FCFS":
            return "FCFS / non-preemptive"
        name = "SJF" if a == "SJF" else "Priority"
        return f"{name} / {'preemptive' if pre else 'non-preemptive'}"

    def _rerun_quiet(self):
        if self.result is not None and self.rows:
            self.run_quiet()
        else:
            self.w.lblMode.setText(self._mode_text())

    def run_quiet(self):
        try:
            self._run()
        except ValidationError as e:
            self.say("Error: " + str(e))

    # ------------------------------------------------------------------ run
    def collect(self):
        procs, seen = [], set()
        if not self.rows:
            raise ValidationError("Add at least one process before running the queue.")
        for i, r in enumerate(self.rows, 1):
            pid, a, b, pr = r.raw()
            if not pid:
                raise ValidationError(f"Row {i}: the process ID is empty.")
            if pid in seen:
                raise ValidationError(f"Duplicate process ID '{pid}'.")
            seen.add(pid)
            arrival = parse_int(a, f"{pid} arrival time", 0)
            burst = parse_int(b, f"{pid} burst time", 1)
            prio = parse_int(pr, f"{pid} priority") if self.algo == "PRIORITY" else 0
            procs.append(Process(pid, arrival, burst, prio))
        return procs

    @safe
    def run(self):
        self._run()

    def _run(self):
        procs = self.collect()
        pre = self.w.chkPreempt.isChecked() and self.algo in ("SJF", "PRIORITY")
        res = schedule(procs, self.algo, self.w.spinQuantum.value(), pre)
        self.procs, self.result = procs, res
        self.colors = {r.raw()[0]: pid_color(i) for i, r in enumerate(self.rows)}
        self.w.lblMode.setText(self._mode_text())
        self.gantt.set_data(res.slices, self.colors)
        self.t0, self.t1 = res.slices[0].start, res.slices[-1].end
        self.t = self.t1
        t = self.w.tblLedger
        t.setRowCount(len(res.metrics))
        for i, m in enumerate(res.metrics):
            for j, v in enumerate((m.pid, m.start, m.finish, m.waiting, m.turnaround)):
                t.setItem(i, j, self._item(v))
        w = self.w
        w.lblAvgWait.setText(f"{res.avg_waiting:.2f} ms")
        w.lblAvgTat.setText(f"{res.avg_turnaround:.2f} ms")
        w.lblBusy.setText(f"{res.cpu_busy * 100:.0f}%")
        w.lblThru.setText(f"{res.throughput:.2f} / ms")
        w.lblState.setText("●   FINISHED")
        self._playback_label()
        self.say(f"{self.algo} complete / {len(procs)} processes / {res.makespan} ms / Order {' → '.join(res.order)}")

    @staticmethod
    def _item(v):
        from PySide6.QtWidgets import QTableWidgetItem
        return QTableWidgetItem(str(v))

    # ------------------------------------------------------------------ playback
    def _playback_label(self):
        if self.result is None:
            return
        done = self.t - self.t0
        total = self.t1 - self.t0
        self.w.lblPlayback.setText(f"Playback {self.prefs.speed:g}× / {done} of {total} ms")

    def first(self):
        if self.result is None:
            return self.say("Run the queue first.")
        self.timer.stop()
        self.t = self.t0
        self.gantt.set_progress(self.t)
        self.w.lblState.setText("●   READY")
        self._playback_label()

    def play(self):
        if self.result is None:
            return self.say("Run the queue first.")
        if self.prefs["motion"]:
            self.t = self.t1
            self.gantt.set_progress(None)
            self._playback_label()
            return
        if self.t >= self.t1:
            self.t = self.t0
        self.w.lblState.setText("●   RUNNING")
        self.timer.start(max(30, int(300 / self.prefs.speed)))

    def _tick(self):
        self.t += 1
        self.gantt.set_progress(self.t if self.t < self.t1 else None)
        self._playback_label()
        if self.t >= self.t1:
            self.timer.stop()
            self.w.lblState.setText("●   FINISHED")

    def step(self):
        if self.result is None:
            return self.say("Run the queue first.")
        self.timer.stop()
        bounds = sorted({s.end for s in self.result.slices})
        nxt = next((b for b in bounds if b > self.t), None)
        if nxt is None:
            self.t = self.t0
            nxt = self.t0
            self.gantt.set_progress(self.t0)
        else:
            self.t = nxt
            self.gantt.set_progress(nxt if nxt < self.t1 else None)
        self.w.lblState.setText("●   FINISHED" if self.t >= self.t1 else "●   STEPPING")
        self._playback_label()

    # ------------------------------------------------------------------ menus
    def menus(self):
        return {
            "File": [("Reset", self.reset), None, ("Export results (CSV)…", self.export)],
            "Processes": [("Add process", self.add_row), ("Edit as text… (paste many)", self.bulk_edit), ("Remove last process", self.remove_last), ("Clear all", self.reset)],
            "Timeline": [("First", self.first), ("Play", self.play), ("Step", self.step), None, ("Show execution order", self.show_order)],
            "Compare policies": [("Compare all algorithms…", self.compare)],
            "Help": [("About this simulator", self.about)],
        }

    def remove_last(self):
        if self.rows:
            self.remove_row(self.rows[-1])

    @safe
    def show_order(self):
        if self.result is None:
            raise ValidationError("Run the queue first.")
        self.show_text("Execution order", " → ".join(self.result.order) + "\n\n" +
                       "\n".join(f"{s.pid or 'idle'}: {s.start} – {s.end}" for s in self.result.slices))

    @safe
    def export(self):
        if self.result is None:
            raise ValidationError("Run the queue before exporting.")
        path = self.pick_save("Export results", "cpu_scheduling.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8") as f:
            wr = csv.writer(f)
            wr.writerow(["Process", "Arrival", "Burst", "Start", "Completion", "Turnaround", "Waiting", "Response"])
            for m in self.result.metrics:
                wr.writerow([m.pid, m.arrival, m.burst, m.start, m.finish, m.turnaround, m.waiting, m.response])
            wr.writerow([]); wr.writerow(["Average waiting", f"{self.result.avg_waiting:.4f}"])
            wr.writerow(["Average turnaround", f"{self.result.avg_turnaround:.4f}"])
        self.say(f"Exported to {path}")

    @safe
    def compare(self):
        procs = self.collect()
        try:
            import matplotlib
            matplotlib.use("QtAgg")
            from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
            from matplotlib.figure import Figure
        except Exception:
            raise ValidationError("Matplotlib is not installed (pip install matplotlib).")
        has_prio = any(p.priority for p in procs) or True
        runs = [("FCFS", schedule(procs, "FCFS")), ("SJF", schedule(procs, "SJF")),
                ("SRTF", schedule(procs, "SJF", preemptive=True)), ("Priority", schedule(procs, "PRIORITY")),
                (f"RR q={self.w.spinQuantum.value()}", schedule(procs, "RR", self.w.spinQuantum.value()))]
        dlg = QDialog(self)
        dlg.setWindowTitle("Compare policies")
        dlg.resize(720, 440)
        lay = QVBoxLayout(dlg)
        fig = Figure(figsize=(7, 4), facecolor=self.pal["bg"])
        ax = fig.add_subplot(111, facecolor=self.pal["surface"])
        xs = range(len(runs))
        ax.bar([x - .2 for x in xs], [r.avg_waiting for _, r in runs], .4, label="Avg waiting", color=self.pal["accent"], edgecolor=self.pal["border"])
        ax.bar([x + .2 for x in xs], [r.avg_turnaround for _, r in runs], .4, label="Avg turnaround", color=PCOL[1], edgecolor=self.pal["border"])
        ax.set_xticks(list(xs)); ax.set_xticklabels([n for n, _ in runs])
        ax.tick_params(colors=self.pal["ink"]); ax.legend()
        ax.set_title("Same processes, different policies", color=self.pal["ink"])
        for sp in ax.spines.values():
            sp.set_color(self.pal["border"])
        lay.addWidget(FigureCanvasQTAgg(fig))
        dlg.exec()

    def about(self):
        self.show_text("CPU scheduling", "Enter processes in the rack (ID, arrival, burst, and priority for Priority scheduling).\n"
                       "Lower priority number = higher priority. Ties are broken by arrival, then input order.\n"
                       "Round Robin queues new arrivals before the pre-empted process.")
