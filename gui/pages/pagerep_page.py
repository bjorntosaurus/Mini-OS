"""Framelog — Page replacement page."""
from PySide6.QtCore import QTimer, Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout

from algorithms.page_replacement import simulate
from gui.pages.base import BasePage, safe
from gui.widgets.charts import FrameHistoryWidget
from gui.widgets.common import clear_layout, mk_label
from utils.validators import ValidationError, parse_int_list


class PageRepPage(BasePage):
    UI = "page_replacement.ui"
    KEY = "pagerep"
    TITLE = "Framelog — Page replacement"
    PATH = "kernel98 / page-replacement"
    ICON = "pagerep"

    def build(self):
        w = self.w
        self.algo, self.frames, self.res = "FIFO", 3, None
        self.hist = FrameHistoryWidget()
        w.histHost.layout().addWidget(self.hist)
        self.hist.stepClicked.connect(self.show_step)
        for b, a in ((w.btnFIFO, "FIFO"), (w.btnLRU, "LRU"), (w.btnOpt, "OPTIMAL")):
            b.clicked.connect(lambda _=False, a=a: self.set_algo(a))
        w.btnReplay.clicked.connect(self.replay)
        w.btnMinus.clicked.connect(lambda: self.set_frames(self.frames - 1))
        w.btnPlus.clicked.connect(lambda: self.set_frames(self.frames + 1))
        w.edRefs.returnPressed.connect(self.replay)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._anim)
        self.set_frames(3, run=False)
        self.hist.pal = self.pal
        self.show_empty()

    def set_frames(self, n, run=True):
        if n < 1:
            return
        self.frames = n
        self.w.lblFrames.setText(f"{n} FRAME{'S' if n != 1 else ''}")
        if run and self.res is not None:
            self.run(animate=False, quiet=True)

    def set_algo(self, a):
        self.algo = a
        w = self.w
        w.btnFIFO.setChecked(a == "FIFO"); w.btnLRU.setChecked(a == "LRU"); w.btnOpt.setChecked(a == "OPTIMAL")
        if self.res is not None:
            self.run(animate=False, quiet=True)

    @safe
    def replay(self):
        self.run(animate=True)

    def run(self, animate=False, quiet=False):
        try:
            refs = parse_int_list(self.w.edRefs.text(), "Reference string", 0)
            res = simulate(refs, self.frames, self.algo)
        except ValidationError as e:
            if quiet:
                return self.say("Error: " + str(e))
            raise
        self.res = res
        self.hist.set_result(res, self.frames)
        self._fill_queue()
        w = self.w
        w.lblNote.setText({"FIFO": "Initially empty / FIFO replaces the oldest resident page.",
                           "LRU": "Initially empty / LRU replaces the least recently used page.",
                           "OPTIMAL": "Initially empty / Optimal replaces the page used farthest in the future."}[self.algo])
        n = len(res.steps)
        w.lblFaults.setText(str(res.faults)); w.lblHits.setText(str(res.hits))
        w.lblHitRatio.setText(f"{res.hit_ratio * 100:.1f}%")
        w.lblFaultRatio.setText(f"Fault ratio: {res.fault_ratio * 100:.1f}%")
        w.lblOldest.setText(res.queue_labels[0]); w.lblNewest.setText(res.queue_labels[1])
        if animate and not self.prefs["motion"]:
            self.hist.set_reveal(0)
            self.shown = 0
            self.timer.start(max(40, int(380 / self.prefs.speed)))
        else:
            self.timer.stop()
            self.show_step(n - 1)
        self.say(f"{self.algo} replay complete / {res.faults} faults / {res.hits} hit{'s' if res.hits != 1 else ''} / "
                 f"Final queue {' → '.join(map(str, res.final_queue))}")

    def _anim(self):
        self.shown += 1
        self.hist.set_reveal(self.shown)
        self.show_step(self.shown - 1, from_anim=True)
        if self.shown >= len(self.res.steps):
            self.timer.stop()

    def show_step(self, i, from_anim=False):
        if not self.res or i < 0:
            return
        st = self.res.steps[i]
        self.hist.set_selected(i)
        w = self.w
        w.lblStep.setText(f"STEP {i + 1:02d} / {len(self.res.steps):02d}")
        w.lblPageBig.setText(f"Page {st.page}")
        w.lblFault.setText("PAGE FAULT" if st.fault else "PAGE HIT")
        w.faultBadge.setProperty("card", "accentbox" if st.fault else "accent")
        w.faultBadge.style().unpolish(w.faultBadge); w.faultBadge.style().polish(w.faultBadge)
        if st.fault and st.evicted is not None:
            w.lblEvict.setText(f"{st.evicted} → {st.page}")
            w.lblEvSub.setText(f"Frame {st.slot + 1} overwritten")
        elif st.fault:
            w.lblEvict.setText("—")
            w.lblEvSub.setText(f"Loaded into empty frame {st.slot + 1}")
        else:
            w.lblEvict.setText("—")
            w.lblEvSub.setText("Page already resident")

    def _fill_queue(self):
        lay = self.w.queueHost.layout()
        clear_layout(lay)
        q = self.res.final_queue
        for k, pg in enumerate(q):
            b = mk_label(str(pg), "h1s")
            b.setAlignment(Qt.AlignCenter)
            b.setFixedSize(112, 56)
            b.setStyleSheet(f"background:{self.pal['surface']};color:{self.pal['ink']};border:2px solid {self.pal['border']};font-size:24px;font-weight:800;")
            lay.addWidget(b)
            if k < len(q) - 1:
                a = mk_label("→", "arrow")
                lay.addWidget(a)

    def themed(self):
        if getattr(self, "res", None):
            self._fill_queue()

    def show_empty(self):
        w = self.w
        w.lblStep.setText("STEP — / —"); w.lblPageBig.setText("—"); w.lblFault.setText("—")
        w.lblEvict.setText("—"); w.lblEvSub.setText(""); w.lblFaults.setText("0"); w.lblHits.setText("0")
        w.lblHitRatio.setText("—"); w.lblFaultRatio.setText("Fault ratio: —"); w.lblNote.setText("Type a reference string, then press Replay.")

    def reset(self):
        self.timer.stop()
        self.w.edRefs.setText("")
        self.res = None
        self.hist.res = None
        self.hist.update()
        clear_layout(self.w.queueHost.layout())
        self.show_empty()
        self.say("Reset. Type a reference string such as 7, 0, 1, 2, 0, 3 and press Replay.")

    @safe
    def compare_all(self):
        refs = parse_int_list(self.w.edRefs.text(), "Reference string", 0)
        lines = []
        for a in ("FIFO", "LRU", "OPTIMAL"):
            r = simulate(refs, self.frames, a)
            lines.append(f"{a:8s}  faults {r.faults:4d}   hits {r.hits:4d}   hit ratio {r.hit_ratio * 100:5.1f}%")
        self.show_text(f"All policies with {self.frames} frames", "\n".join(lines))

    def menus(self):
        return {"File": [("Reset", self.reset)],
                "Reference string": [("Replay", self.replay)],
                "Replacement policy": [("FIFO", lambda: self.set_algo("FIFO")), ("LRU", lambda: self.set_algo("LRU")),
                                       ("Optimal", lambda: self.set_algo("OPTIMAL")), None, ("Compare all policies…", self.compare_all)],
                "Frame history": [("Add frame", lambda: self.set_frames(self.frames + 1)), ("Remove frame", lambda: self.set_frames(self.frames - 1))],
                "Help": [("About", lambda: self.show_text("Page replacement", "Type any number of page references separated by commas or spaces.\n"
                         "Green columns are hits; click a column to inspect that step. A new page takes the frame slot of its victim."))]}
