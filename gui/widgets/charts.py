"""Custom-painted visualisations (Gantt, frame history, disk route, memory map, curve, ...)."""
from PySide6.QtCore import QPointF, QRectF, Qt, Signal, QSize
from PySide6.QtGui import QBrush, QColor, QPainter, QPen, QPolygonF
from PySide6.QtWidgets import QSizePolicy

from gui.widgets.common import PalWidget


def _pen(color, w=2):
    p = QPen(QColor(color))
    p.setWidthF(w)
    p.setJoinStyle(Qt.MiterJoin)
    return p


class GanttWidget(PalWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.slices, self.colors, self.progress = [], {}, None
        self.setMinimumHeight(96)

    def set_data(self, slices, colors):
        self.slices, self.colors, self.progress = slices, colors, None
        self.update()

    def set_progress(self, t):
        self.progress = t
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, False)
        w, h = self.width() - 6, self.height()
        if not self.slices:
            p.setPen(self.c("muted"))
            p.setFont(self.mono(11))
            p.drawText(self.rect(), Qt.AlignCenter, "Run the queue to draw the timeline")
            return
        t0, t1 = self.slices[0].start, self.slices[-1].end
        span = max(1, t1 - t0)
        sx = lambda t: 2 + (t - t0) / span * w
        top, bh = 8, max(40, h - 44)
        last_label = -100
        marks = sorted({s.start for s in self.slices} | {t1})
        for s in self.slices:
            if self.progress is not None and s.start >= self.progress:
                break
            end = s.end if self.progress is None else min(s.end, self.progress)
            r = QRectF(sx(s.start), top, sx(end) - sx(s.start), bh)
            if s.pid is None:
                p.setBrush(QBrush(self.c("soft"), Qt.BDiagPattern))
            else:
                p.setBrush(QColor(self.colors.get(s.pid, "#ccc")))
            p.setPen(_pen(self.pal["border"], 2))
            p.drawRect(r)
            if r.width() > 24:
                p.setPen(QColor("#1d2a22") if s.pid else self.c("muted"))
                p.setFont(self.sans(16 if r.width() > 40 else 11, True))
                p.drawText(r.adjusted(10, 0, -2, 0), Qt.AlignVCenter | Qt.AlignLeft, s.pid or "idle")
        p.setPen(self.c("muted"))
        p.setFont(self.mono(10))
        for t in marks:
            if self.progress is not None and t > self.progress:
                break
            x = sx(t)
            lab = f"{t} ms" if t == t1 else str(t)
            tw = 8 + 7 * len(lab)
            if x - last_label < tw and t != t1:
                continue
            x_txt = min(x, self.width() - tw + 2) if t == t1 else x
            p.drawText(QPointF(x_txt if t != t1 else x - tw + 6, top + bh + 22), lab)
            last_label = x

    def sizeHint(self):
        return QSize(400, 110)


class FrameHistoryWidget(PalWidget):
    stepClicked = Signal(int)
    CELL, GAP, LEFT = 50, 12, 74

    def __init__(self, parent=None):
        super().__init__(parent)
        self.res, self.reveal, self.sel = None, 0, -1
        self.nframes = 0

    def set_result(self, res, nframes):
        self.res, self.nframes = res, nframes
        self.reveal, self.sel = len(res.steps), len(res.steps) - 1
        self._resize()
        self.update()

    def set_reveal(self, n):
        self.reveal = n
        self.sel = n - 1
        self.update()

    def set_selected(self, i):
        self.sel = i
        self.update()

    def _resize(self):
        n = len(self.res.steps) if self.res else 0
        self.setMinimumSize(self.LEFT + n * (self.CELL + self.GAP) + 10, 56 + self.nframes * (self.CELL - 10 + 10) + 40)

    def _col_x(self, i):
        return self.LEFT + i * (self.CELL + self.GAP)

    def mousePressEvent(self, ev):
        if not self.res:
            return
        i = int((ev.position().x() - self.LEFT) // (self.CELL + self.GAP))
        if 0 <= i < self.reveal:
            self.sel = i
            self.stepClicked.emit(i)
            self.update()

    def paintEvent(self, e):
        if not self.res:
            return
        p = QPainter(self)
        rh = 38
        p.setFont(self.mono(9))
        p.setPen(self.c("muted"))
        p.drawText(0, 6, self.LEFT, 24, Qt.AlignVCenter, "REF")
        for r in range(self.nframes):
            p.drawText(0, 40 + r * (rh + 10), self.LEFT, rh, Qt.AlignVCenter, f"FRAME {r + 1}")
        ev_y = 40 + self.nframes * (rh + 10) + 2
        p.drawText(0, ev_y, self.LEFT, 24, Qt.AlignVCenter, "EVENT")
        for i, st in enumerate(self.res.steps[:self.reveal]):
            x = self._col_x(i)
            p.setPen(self.c("ink"))
            p.setFont(self.mono(15, True))
            p.drawText(x, 6, self.CELL, 24, Qt.AlignCenter, str(st.page))
            selected = i == self.sel
            for r in range(self.nframes):
                v = st.frames[r]
                rect = QRectF(x, 40 + r * (rh + 10), self.CELL, rh)
                fill = self.c("surface")
                if not st.fault:
                    fill = QColor(self.pal["hit"])
                elif selected:
                    fill = self.c("accent")
                p.setBrush(fill)
                p.setPen(_pen(self.pal["border"], 3 if selected else 2))
                p.drawRect(rect)
                p.setPen(QColor("#1d2a22") if fill != self.c("surface") else self.c("ink"))
                p.setFont(self.mono(15))
                p.drawText(rect, Qt.AlignCenter, "–" if v is None else str(v))
            p.setFont(self.mono(11, True))
            p.setPen(self.c("ink") if st.fault else self.c("muted"))
            p.drawText(x, ev_y, self.CELL, 24, Qt.AlignCenter, "F" if st.fault else "H")

    def sizeHint(self):
        return self.minimumSize()


class DiskPlotWidget(PalWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.path, self.labels, self.lo, self.hi = [], [], 0, 199
        self.setMinimumHeight(260)

    def set_data(self, path, labels, lo, hi):
        self.path, self.labels, self.lo, self.hi = path, labels, lo, hi
        self.setMinimumHeight(max(260, 50 + len(path) * 30))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing, True)
        if not self.path:
            return
        L, R, T, step = 34, 60, 30, 30
        w = max(50, self.width() - L - R)
        sx = lambda c: L + (c - self.lo) / max(1, self.hi - self.lo) * w
        p.setFont(self.mono(9))
        ticks = [self.lo + round(i * (self.hi - self.lo) / 4) for i in range(5)]
        for t in ticks:
            x = sx(t)
            p.setPen(_pen(self.pal["grid"], 1))
            p.drawLine(int(x), T - 6, int(x), T + step * len(self.path) - 14)
            p.setPen(self.c("muted"))
            p.drawText(QPointF(x - 9, 12), str(t))
        pts = [QPointF(sx(c), T + i * step) for i, c in enumerate(self.path)]
        p.setPen(_pen("#4d5aa8" if self.pal.get("mode") == "light" else self.pal["accent"], 2.5))
        for a, b in zip(pts, pts[1:]):
            p.drawLine(a, b)
        for i, (pt, c) in enumerate(zip(pts, self.path)):
            p.setPen(self.c("muted"))
            p.setFont(self.mono(9))
            p.drawText(QPointF(2, pt.y() + 3), self.labels[i])
            p.setBrush(self.c("accent"))
            p.setPen(_pen(self.pal["border"], 2))
            p.drawRect(QRectF(pt.x() - 5, pt.y() - 5, 10, 10))
            p.setPen(self.c("ink"))
            p.drawText(QPointF(pt.x() + 9, pt.y() + 4), str(c))


class MemorySpaceWidget(PalWidget):
    segmentClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.segs, self.colors, self.selected, self.end = [], {}, None, 1000
        self._rects = []
        self.setMinimumHeight(300)

    def set_data(self, segs, colors, selected, end):
        self.segs, self.colors, self.selected, self.end = segs, colors, selected, end
        self.update()

    def mousePressEvent(self, ev):
        for sid, r in self._rects:
            if r.contains(ev.position()):
                self.segmentClicked.emit(sid)
                return

    def paintEvent(self, e):
        p = QPainter(self)
        L, T, B = 56, 8, 12
        W, H = self.width() - L - 4, self.height() - T - B
        self._rects = []
        if not self.segs:
            p.setPen(self.c("muted"))
            p.drawText(self.rect(), Qt.AlignCenter, "No segments defined")
            return
        sy = lambda a: T + a / self.end * H
        p.setBrush(QColor(self.pal["soft"]))
        p.setPen(_pen(self.pal["border"], 2))
        p.drawRect(QRectF(L, T, W, H))
        p.setFont(self.mono(9))
        labelled = []
        for s in sorted(self.segs, key=lambda s: s.base):
            y0, y1 = sy(s.base), sy(s.base + s.limit)
            r = QRectF(L, y0, W, max(16, y1 - y0))
            p.setBrush(QColor(self.colors.get(s.seg_id, "#ccc")))
            p.setPen(_pen(self.pal["border"], 3 if s.seg_id == self.selected else 2))
            p.drawRect(r)
            p.setPen(QColor("#1d2a22"))
            p.setFont(self.sans(11, True))
            p.drawText(r.adjusted(8, 0, 0, 0), Qt.AlignVCenter, f"{s.name or 'Seg ' + str(s.seg_id)} / {s.limit:,} B")
            self._rects.append((s.seg_id, r))
            labelled.append(s.base)
        p.setFont(self.mono(9))
        p.setPen(self.c("muted"))
        last_y = -100
        for a in sorted({0, self.end, *labelled}):
            y = sy(a)
            if y - last_y >= 13 or a == self.end:
                p.drawText(QPointF(2, min(y + 10 if a == 0 else y + 4, T + H)), f"{a:,}")
                last_y = y

    def sizeHint(self):
        return QSize(300, 320)


class CurveWidget(PalWidget):
    nClicked = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.p, self.n, self.maxn = 0.8, 4, 8
        self.setMinimumHeight(170)

    def set_data(self, p, n, maxn=8):
        self.p, self.n, self.maxn = p, n, max(maxn, n, 2)
        self.update()

    def _geom(self):
        return 50, 14, self.width() - 66, self.height() - 52

    def mousePressEvent(self, ev):
        L, T, W, H = self._geom()
        k = round((ev.position().x() - L) / W * (self.maxn - 1)) + 1
        if 1 <= k <= self.maxn:
            self.nClicked.emit(k)

    def paintEvent(self, e):
        pa = QPainter(self)
        pa.setRenderHint(QPainter.Antialiasing, True)
        L, T, W, H = self._geom()
        pa.setFont(self.mono(9))
        for i, lab in enumerate(("100%", "75%", "50%", "25%", "0%")):
            y = T + H * i / 4
            pa.setPen(_pen(self.pal["grid"], 1))
            pa.drawLine(L, int(y), L + W, int(y))
            pa.setPen(self.c("muted"))
            pa.drawText(QPointF(4, y + 3), lab)
        pts = []
        for k in range(1, self.maxn + 1):
            u = 1 - self.p ** k
            pts.append(QPointF(L + (k - 1) / (self.maxn - 1) * W, T + H * (1 - u)))
            pa.setPen(self.c("muted"))
            pa.drawText(QPointF(pts[-1].x() - 3, T + H + 18), str(k))
        pa.drawText(QPointF(L + W / 2 - 80, T + H + 36), "DEGREE OF MULTIPROGRAMMING →")
        line = QColor("#4f6b2a") if self.pal.get("mode") == "light" else QColor(self.pal["accent"])
        pa.setPen(_pen(line.name(), 2.5))
        for a, b in zip(pts, pts[1:]):
            pa.drawLine(a, b)
        for k, pt in enumerate(pts, 1):
            pa.setBrush(QColor(self.pal["accent"]))
            pa.setPen(_pen(line.name(), 2))
            if k == self.n:
                pa.drawEllipse(pt, 9, 9)
                pa.setPen(self.c("ink"))
                pa.setFont(self.mono(10, True))
                pa.drawText(QPointF(pt.x() - 56, pt.y() - 16), f"n = {k} / {(1 - self.p ** k) * 100:.2f}%")
                pa.setFont(self.mono(9))
            else:
                pa.drawRect(QRectF(pt.x() - 4, pt.y() - 4, 8, 8))


STATE_COL = {"R": "#c4f06a", "Y": "#ffcc62", "W": "#ffa3c4", "Q": "#c5b3f2", "D": None, "-": None}


class StateTimelineWidget(PalWidget):
    cellClicked = Signal(int)
    LEFT = 64

    def __init__(self, parent=None):
        super().__init__(parent)
        self.names, self.states, self.tick, self.cw = [], [], None, 12

    def set_data(self, names, states):
        self.names, self.states = names, states
        n = len(states[0]) if states else 0
        self.setMinimumSize(self.LEFT + n * 6 + 10, 24 + len(names) * 22 + 28)
        self.update()

    def set_tick(self, t):
        self.tick = t
        self.update()

    def mousePressEvent(self, ev):
        if self.states:
            n = len(self.states[0])
            cw = (self.width() - self.LEFT - 6) / max(1, n)
            k = int((ev.position().x() - self.LEFT) // cw)
            if 0 <= k < n:
                self.cellClicked.emit(k)

    def paintEvent(self, e):
        p = QPainter(self)
        if not self.states:
            p.setPen(self.c("muted"))
            p.setFont(self.mono(11))
            p.drawText(self.rect(), Qt.AlignCenter, "Press “Run simulation”")
            return
        n = len(self.states[0])
        cw = (self.width() - self.LEFT - 6) / n
        p.setFont(self.mono(9))
        for r, (name, st) in enumerate(zip(self.names, self.states)):
            y = 6 + r * 22
            p.setPen(self.c("ink"))
            p.drawText(0, y, self.LEFT - 6, 18, Qt.AlignVCenter, name[:9])
            for k, ch in enumerate(st):
                col = STATE_COL.get(ch)
                x = self.LEFT + k * cw
                if col:
                    p.fillRect(QRectF(x, y, max(1.0, cw - (1 if cw > 3 else 0)), 18), QColor(col))
                elif ch == "D":
                    p.fillRect(QRectF(x, y + 8, max(1.0, cw - 1), 2), self.c("grid"))
        y = 6 + len(self.names) * 22 + 8
        x = self.LEFT
        fm = p.fontMetrics()
        for ch, lab in (("R", "running"), ("Y", "ready"), ("W", "I/O wait"), ("Q", "queued (no memory)")):
            p.fillRect(QRectF(x, y, 12, 12), QColor(STATE_COL[ch]))
            p.setPen(self.c("muted"))
            p.drawText(QPointF(x + 16, y + 10), lab)
            x += 16 + fm.horizontalAdvance(lab) + 18
        if self.tick is not None and 0 <= self.tick < n:
            p.setPen(_pen(self.pal["border"], 2))
            xm = self.LEFT + self.tick * cw + cw / 2
            p.drawLine(int(xm), 2, int(xm), 6 + len(self.names) * 22)


class SplitBar(PalWidget):
    """Two-part bar: used (cyan) | wasted (accent)."""

    def __init__(self, parent=None, used_color="#84d9e0"):
        super().__init__(parent)
        self.ratio, self.used_color = 0.5, used_color
        self.setFixedHeight(26)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

    def set_ratio(self, r):
        self.ratio = max(0.0, min(1.0, r))
        self.update()

    def paintEvent(self, e):
        p = QPainter(self)
        w, h = self.width() - 2, self.height() - 2
        used = w * self.ratio
        p.setPen(Qt.NoPen)
        p.fillRect(QRectF(1, 1, used, h), QColor(self.used_color))
        p.fillRect(QRectF(1 + used, 1, w - used, h), self.c("accent"))
        p.setBrush(Qt.NoBrush)
        p.setPen(_pen(self.pal["border"], 2))
        p.drawRect(QRectF(1, 1, w, h))
        if 0 < used < w:
            p.drawLine(QPointF(1 + used, 1), QPointF(1 + used, h + 1))


class ThemePreview(PalWidget):
    """Little window mock-up used on the Settings screen."""

    def __init__(self, dark, parent=None):
        super().__init__(parent)
        self.dark = dark
        self.setAttribute(Qt.WA_TransparentForMouseEvents)

    def paintEvent(self, e):
        p = QPainter(self)
        d = self.dark
        desk, win, bar, side, ink = (("#12303a", "#2a3437", "#1a2326", "#1f272a", "#0a1517") if d else
                                     ("#2b6a70", "#f4f4e9", "#d1d8c3", "#e6e8db", "#1d2a22"))
        r = self.rect().adjusted(8, 8, -8, -8)
        p.fillRect(r, QColor(desk))
        p.setPen(_pen(ink, 2))
        p.drawRect(r)
        w = QRectF(r.x() + r.width() * .22, r.y() + r.height() * .1, r.width() * .56, r.height() * .62)
        p.setBrush(QColor(win))
        p.drawRect(w)
        p.fillRect(QRectF(w.x() + 1, w.y() + 1, w.width() - 2, 12), QColor(bar))
        p.fillRect(QRectF(w.x() + 1, w.y() + 13, w.width() * .22, w.height() - 14), QColor(side))
        for i, col in enumerate(("#c4f06a", "#ffa3c4", "#c5b3f2")):
            bx = QRectF(w.x() + w.width() * .32 + i * (w.width() * .22), w.y() + w.height() * .38, w.width() * .17, w.height() * .2)
            p.setBrush(QColor(col))
            p.drawRect(bx)
        p.fillRect(QRectF(r.x() + 1, r.bottom() - 14, r.width() - 2, 13), QColor(bar))
