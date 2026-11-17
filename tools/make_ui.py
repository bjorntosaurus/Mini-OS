"""Generates the Qt Designer .ui files in ../ui.  Run:  python tools/make_ui.py
The generated files are normal .ui files: open them with `pyside6-designer ui/cpu_scheduling.ui`,
edit them freely and the app will pick the changes up (widgets are found by objectName).
(If you regenerate with this script, your Designer edits to that file are overwritten.)"""
import os
from xml.sax.saxutils import escape

_n = [0]
BARE = ("QScrollArea", "QStackedWidget")


def _u(prefix):
    _n[0] += 1
    return f"{prefix}{_n[0]}"


class Node:
    def __init__(self, cls, name, text=None, **o):
        self.cls, self.name, self.text, self.o = cls, name, text, o


def W(cls, name, text=None, **o):
    return Node(cls, name, text, **o)


def S(v=False):
    return Node("spacer", _u("spacer"), None, vertical=v)


def prop(name, kind, val, dyn=False):
    v = ("true" if val else "false") if kind == "bool" else escape(str(val))
    return f'<property name="{name}"{" stdset=\"0\"" if dyn else ""}><{kind}>{v}</{kind}></property>'


def emit(n, ind=2):
    pad = " " * ind
    if n.cls == "spacer":
        o = "Qt::Vertical" if n.o.get("vertical") else "Qt::Horizontal"
        return (f'{pad}<spacer name="{n.name}"><property name="orientation"><enum>{o}</enum></property>'
                f'<property name="sizeHint" stdset="0"><size><width>20</width><height>20</height></size></property></spacer>')
    o = n.o
    out = [f'{pad}<widget class="{n.cls}" name="{n.name}">']
    P = []
    if n.text is not None:
        P.append(prop("text", "string", n.text) if n.cls != "QLineEdit" else prop("text", "string", n.text))
    if o.get("ph"):
        P.append(prop("placeholderText", "string", o["ph"]))
    for k in ("checkable", "checked", "editable", "wordWrap", "flat"):
        if k in o:
            P.append(prop(k, "bool", o[k]))
    if o.get("excl"):
        P.append(prop("autoExclusive", "bool", True))
    if n.cls in BARE or n.cls == "QScrollArea":
        pass
    if n.cls == "QScrollArea":
        P.append(prop("widgetResizable", "bool", True))
        P.append(prop("frameShape", "enum", "QFrame::NoFrame"))
    for k, nm in (("minw", "minimumWidth"), ("minh", "minimumHeight")):
        pass
    sz = lambda k, w, h: f'<property name="{k}"><size><width>{w}</width><height>{h}</height></size></property>'
    if "fixw" in o or "fixh" in o:
        fw, fh = o.get("fixw"), o.get("fixh")
        if fw is not None and fh is not None:
            P.append(sz("minimumSize", fw, fh)); P.append(sz("maximumSize", fw, fh))
        elif fw is not None:
            P.append(sz("minimumSize", fw, o.get("minh", 0))); P.append(sz("maximumSize", fw, 16777215))
        else:
            P.append(sz("minimumSize", o.get("minw", 0), fh)); P.append(sz("maximumSize", 16777215, fh))
    elif "minw" in o or "minh" in o:
        P.append(sz("minimumSize", o.get("minw", 0), o.get("minh", 0)))
    if "rng" in o:
        P.append(prop("minimum", "number", o["rng"][0])); P.append(prop("maximum", "number", o["rng"][1]))
    if "val" in o:
        P.append(prop("value", "number", o["val"]))
    if o.get("orient"):
        P.append(f'<property name="orientation"><enum>Qt::{o["orient"]}</enum></property>')
    for k, v in o.get("dyn", {}).items():
        P.append(prop(k, "string", v, dyn=True))
    out += [pad + "  " + p for p in P]
    for it in o.get("items", []):
        out.append(f'{pad}  <item><property name="text"><string>{escape(it)}</string></property></item>')
    kids = o.get("kids", [])
    lay = o.get("lay")
    if kids and n.cls in BARE:
        out += [emit(k, ind + 2) for k in kids]
    elif lay:
        cls = {"V": "QVBoxLayout", "H": "QHBoxLayout", "G": "QGridLayout"}[lay]
        st = f' stretch="{o["stretch"]}"' if o.get("stretch") else ""
        out.append(f'{pad}  <layout class="{cls}" name="{_u("layout")}"{st}>')
        m = o.get("m", (0, 0, 0, 0))
        for nm, v in zip(("leftMargin", "topMargin", "rightMargin", "bottomMargin"), m):
            out.append(f'{pad}    {prop(nm, "number", v)}')
        out.append(f'{pad}    {prop("spacing", "number", o.get("sp", 6))}')
        for k in kids:
            if lay == "G":
                node, r, c, *rest = k
                rs, cs = (rest + [1, 1])[:2] if rest else (1, 1)
                out.append(f'{pad}    <item row="{r}" column="{c}" rowspan="{rs}" colspan="{cs}">')
                out.append(emit(node, ind + 6))
            else:
                al = ""
                if isinstance(k, tuple):
                    k, al = k
                out.append(f'{pad}    <item{al}>')
                out.append(emit(k, ind + 6))
            out.append(f'{pad}    </item>')
        out.append(f'{pad}  </layout>')
    out.append(f"{pad}</widget>")
    return "\n".join(out)


def save(fname, root):
    xml = ('<?xml version="1.0" encoding="UTF-8"?>\n<ui version="4.0">\n <class>Form</class>\n'
           + emit(root, 1) + '\n <resources/>\n <connections/>\n</ui>\n')
    os.makedirs("ui", exist_ok=True)
    open(os.path.join("ui", fname), "w", encoding="utf-8").write(xml)


# ------------------------------------------------------------------ helpers
def L(name, text, kind=None, wrap=False, **o):
    d = {"kind": kind} if kind else {}
    d.update(o.pop("dyn", {}))
    return W("QLabel", name, text, dyn=d, wordWrap=wrap, **o)


def B(name, text, role=None, **o):
    d = {"role": role} if role else {}
    return W("QPushButton", name, text, dyn=d, **o)


def F(name, kids, lay="V", card=None, m=(14, 12, 14, 12), sp=6, **o):
    d = {"card": card} if card else {}
    d.update(o.pop("dyn", {}))
    return W("QFrame", name, dyn=d, lay=lay, kids=kids, m=m, sp=sp, **o)


def C(name, kids, lay="V", m=(0, 0, 0, 0), sp=6, **o):
    return W("QWidget", name, lay=lay, kids=kids, m=m, sp=sp, **o)


def page(kids, m=(22, 16, 22, 10), sp=12, name="page"):
    return W("QWidget", name, lay="V", kids=kids, m=m, sp=sp)


def title_block(t, sub):
    return C("titleBlock", [L("lblTitle", t, "h1"), L("lblSub", sub, "eyebrow")], sp=2)


# ------------------------------------------------------------------ sidebar (home + settings)
SIM_NAMES = ["CPU sched.", "Banker’s algo.", "Paging", "Page replace.", "Segmentation", "Fragmentation", "Disk sched.", "Multiprog."]


def sidebar():
    kids = [L("lblWs", "WORKSPACE", "eyebrow"), B("navHome", "⌂  My computer", "nav", checkable=True),
            L("lblSims", "SIMULATORS / 08", "eyebrow", dyn={"gap": "1"})]
    kids += [B(f"nav{i}", t, "nav", checkable=True) for i, t in enumerate(SIM_NAMES)]
    kids += [L("lblPrefs", "PREFERENCES", "eyebrow", dyn={"gap": "1"}), B("navSettings", "Settings", "nav", checkable=True), S(True),
             F("sysReady", [L("lblSys", "●  SYSTEM READY", "mono"), L("lblVer", "v.1.0 / all local", "eyebrow")], card="plain", m=(10, 8, 10, 8), sp=2)]
    return F("sidebar", kids, card="side", m=(8, 12, 8, 12), sp=2, fixw=175)


# ------------------------------------------------------------------ main window
def main_window():
    topbar = F("topbar", [L("lblLogo", "▦  KERNEL / 98", "top"), W("QPushButton", "menuFile", "File", dyn={"role": "top"}),
                          W("QPushButton", "menuView", "View", dyn={"role": "top"}),
                          W("QPushButton", "menuApps", "Applications", dyn={"role": "top"}),
                          W("QPushButton", "menuHelp", "Help", dyn={"role": "top"}), S(),
                          L("lblSession", "●  LOCAL SESSION     /     STUDENT", "top")],
               lay="H", m=(16, 0, 28, 0), sp=22, fixh=32)
    title = F("titlebar", [L("lblTitleIcon", "▣", "wintitle"), L("lblTitle", "My computer — Kernel / 98", "wintitle"), S(),
                           B("btnMin", "–", "win"), B("btnMax", "□", "win"), B("btnClose", "×", "win")],
              lay="H", m=(10, 0, 8, 0), sp=6, fixh=30)
    menubar = F("menubar", [C("menuHost", [], lay="H", sp=26), S(), L("lblPath", "kernel98 / home", "path")],
                lay="H", m=(12, 0, 38, 0), sp=0, fixh=30)
    status = F("statusbar", [L("lblStatus", "Ready. Choose an app to start exploring.", "status"), S(),
                             L("lblKernel", "KERNEL / 98      •      OS LAB", "status")],
               lay="H", m=(12, 0, 38, 0), sp=0, fixh=24)
    win = F("windowFrame", [title, menubar, W("QStackedWidget", "stack"), status], card="window", m=(0, 0, 0, 0), sp=0)
    desktop = W("QWidget", "desktop", lay="H", m=(0, 0, 0, 0), sp=0, stretch="0,1", kids=[
        C("iconCol", [], lay="V", m=(0, 16, 0, 8), sp=10, fixw=142),
        W("QWidget", "winArea", lay="G", m=(0, 0, 0, 0), sp=0, kids=[(win, 0, 0)])])
    taskbar = F("taskbar", [B("btnStart", "▦  Start", "start"), B("btnTask", "▦   Desktop", "task"),
                            L("lblApps", "8 apps installed", "mono"), S(),
                            L("lblOffline", "●  Offline", "mono"), L("lblSound", "♫", "mono"), L("lblClock", "09:41 AM", "mono")],
                lay="H", m=(8, 0, 36, 0), sp=24, fixh=44)
    save("main_window.ui", W("QWidget", "MainWindow", lay="V", m=(0, 0, 0, 0), sp=0, stretch="0,1,0",
                             kids=[topbar, desktop, taskbar]))


# ------------------------------------------------------------------ home
def home():
    content = C("content", [
        L("lblEyebrow", "YOUR PERSONAL OS PLAYGROUND", "eyebrow"),
        C("heroRow", [C("heroText", [L("lblHero", "Your little OS lab.", "hero"),
                                     L("lblHeroSub", "Eight big concepts. One tiny desktop. Open an app and see what happens.", "muted")], sp=4),
                      S(), F("badgeReady", [L("lblReady", "08 / APPS READY", "mono")], card="accent", m=(22, 16, 22, 16), fixh=62)], lay="H", sp=0),
        C("appsHdr", [L("lblApps", "APPLICATIONS", "eyebrow"), S(), L("lblHint", "Double-click an icon to explore ↗", "eyebrow")], lay="H"),
        W("QWidget", "gridHost", lay="G", kids=[], m=(0, 0, 0, 0), sp=12),
        F("newHere", [C("newText", [L("lblNew", "NEW HERE?", "eyebrow"), L("lblNewTitle", "Bring your own data. Run it. Learn by doing.", "h2")], sp=4),
                      S(), B("btnStart", "Start with CPU scheduling →", "primary", fixw=212, fixh=42)],
          lay="H", card="plain", m=(22, 14, 22, 14)),
        L("lblFooter", "100% offline        /        No sign-up        /        Built for curious minds", "eyebrow"),
        S(True)], m=(24, 22, 24, 6), sp=14)
    save("home.ui", W("QWidget", "page", lay="H", m=(0, 0, 0, 0), sp=0, stretch="0,1", kids=[sidebar(), content]))


# ------------------------------------------------------------------ settings
def settings():
    appear = F("cardAppear", [L("lblA", "Appearance", "h3"), L("lblA2", "Choose how Kernel / 98 looks on your desktop.", "muted"),
                              C("themeRow", [B("btnLight", "", "theme", checkable=True, excl=True, checked=True, minh=150),
                                             B("btnDark", "", "theme", checkable=True, excl=True, minh=150)], lay="H", sp=16)],
               card="plain", m=(14, 12, 14, 14), sp=6)
    desk = F("cardDesktop", [L("lblD", "Desktop", "h3"),
                             C("accRow", [L("lblAcc", "Accent color", "muted"), S()] +
                               [B(f"acc{i}", "", "swatch", checkable=True, excl=True, fixw=28, fixh=28) for i in range(5)], lay="H", sp=8),
                             C("soundRow", [C("soundTxt", [L("lblSnd", "UI sounds", "body"), L("lblSnd2", "Little clicks, big nostalgia.", "muted")], sp=0),
                                            S(), B("tglSounds", "ON", "toggle", checkable=True, checked=True, fixw=60, fixh=26)], lay="H"),
                             C("motionRow", [L("lblMo", "Reduced motion", "body"), S(), B("tglMotion", "OFF", "toggle", checkable=True, fixw=60, fixh=26)], lay="H"),
                             S(True)], card="plain", m=(14, 12, 14, 12), sp=10)
    sim = F("cardSim", [L("lblS", "Simulation", "h3"),
                        C("spdRow", [L("lblSp", "Playback speed", "body"), S(), W("QComboBox", "cmbSpeed", items=["0.5× Slow", "1× Normal", "2× Fast", "4× Turbo"], minw=150)], lay="H"),
                        C("tipRow", [L("lblTip", "Show learning tips", "body"), S(), B("tglTips", "ON", "toggle", checkable=True, checked=True, fixw=60, fixh=26)], lay="H"),
                        S(True)], card="plain", m=(14, 12, 14, 12), sp=10)
    content = C("content", [
        L("lblEyebrow", "CONTROL PANEL / PREFERENCES", "eyebrow"), L("lblHero", "Make yourself at home.", "hero"),
        L("lblHeroSub", "Your desktop, your rules. A little nostalgia goes a long way.", "muted"), appear,
        C("row2", [desk, sim], lay="H", sp=18, stretch="1,1"),
        C("foot", [L("lblNote", "Changes apply to all eight apps.", "eyebrow"), S(), B("btnRestore", "Restore defaults", "plain", fixw=146, fixh=42),
                   B("btnSave", "Save preferences", "primary", fixw=150, fixh=42)], lay="H", sp=14),
        S(True)], m=(24, 22, 24, 6), sp=8)
    save("settings.ui", W("QWidget", "page", lay="H", m=(0, 0, 0, 0), sp=0, stretch="0,1", kids=[sidebar(), content]))


# ------------------------------------------------------------------ CPU scheduling
def cpu():
    rack = F("rack", [L("lblRack", "PROCESS RACK", "eyebrow"), L("lblCount", "04 ready processes", "h2"),
                      W("QScrollArea", "scrollRack", kids=[W("QWidget", "rackContent", lay="V", m=(0, 4, 4, 4), sp=10)]),
                      B("btnAdd", "+ Add process", "primary", fixh=40)], card="shadow", m=(14, 14, 14, 14), sp=10, fixw=250)
    algo = C("algoRow", [B("btnFCFS", "FCFS", "seg", checkable=True, excl=True, checked=True, fixh=38, minw=96),
                         B("btnSJF", "SJF", "seg", checkable=True, excl=True, fixh=38, minw=96),
                         B("btnRR", "Round robin", "seg", checkable=True, excl=True, fixh=38, minw=96),
                         B("btnPriority", "Priority", "seg", checkable=True, excl=True, fixh=38, minw=96),
                         S(), W("QCheckBox", "chkPreempt", "Preemptive"), L("lblQ", "Quantum", "eyebrow"),
                         W("QSpinBox", "spinQuantum", rng=(1, 1000000), val=2, fixw=64, fixh=30),
                         B("btnRun", "▶  Run queue", "primary", fixh=38, minw=132)], lay="H", sp=10)
    timeline = F("timeline", [C("tlHead", [L("lblTl", "EXECUTION TIMELINE", "eyebrow"), S(), L("lblMode", "FCFS / non-preemptive", "eyebrow")], lay="H"),
                              W("QWidget", "ganttHost", lay="V", m=(0, 0, 0, 0), sp=0, minh=96),
                              C("tlFoot", [B("btnFirst", "First", "link"), L("sep1", "|", "eyebrow"), B("btnPlay", "Play", "link"),
                                           L("sep2", "|", "eyebrow"), B("btnStep", "Step", "link"), S(),
                                           L("lblPlayback", "Playback 1× / 11 of 11 ms", "eyebrow")], lay="H", sp=10)],
                 card="shadow", m=(18, 14, 18, 12), sp=6)
    ledger = F("ledger", [L("lblLed", "TIMING LEDGER", "eyebrow"), W("QTableWidget", "tblLedger")], card="shadow", m=(18, 14, 18, 10), sp=6)
    stats = C("stats", [F(f"stat{i}", [L(f"lbl{n}", v, "stat"), L(f"cap{n}", c, "eyebrow")], card="shadow" if i != 2 else "accent", m=(14, 10, 14, 8), sp=4, fixh=66)
                        for i, (n, v, c) in enumerate([("AvgWait", "—", "AVG WAIT"), ("AvgTat", "—", "AVG TURNAROUND"), ("Busy", "—", "CPU BUSY"), ("Thru", "—", "THROUGHPUT")])],
              lay="H", sp=18)
    body = C("body", [rack, C("right", [algo, timeline, ledger], sp=12, stretch="0,0,1")], lay="H", sp=16, stretch="0,1")
    hdr = C("hdr", [title_block("DISPATCH", "CPU SCHEDULING / TIMELINE WORKSTATION"), S(),
                    F("badge", [L("lblState", "●   READY", "mono")], card="accent", m=(20, 6, 20, 6), fixh=32)], lay="H")
    save("cpu_scheduling.ui", page([hdr, body, stats]))


# ------------------------------------------------------------------ Banker's
def bankers():
    left = F("sandbox", [L("lblBand", "REQUEST SANDBOX", "band"),
                         C("sbBody", [L("lblT", "Test before you grant.", "h2", wrap=True), L("lblPr", "Process", "muted"),
                                      W("QComboBox", "cmbProc", minh=34), L("lblRv", "REQUEST VECTOR / A · B · C", "eyebrow"),
                                      W("QWidget", "reqHost", lay="H", m=(0, 0, 0, 0), sp=8, minh=64),
                                      B("btnCheck", "Check this request →", "primary", fixh=40),
                                      L("lblPrev", "PREVIEW ONLY", "eyebrow", dyn={"gap": "1"}),
                                      L("lblPreview", "The matrix shows the original resource snapshot. Check a request before committing an allocation.", "small", wrap=True),
                                      B("btnApply", "Apply granted request", "plain", fixh=34), S(True),
                                      L("lblFormula", "Need = Maximum − Allocated", "eyebrow")], m=(16, 14, 16, 14), sp=8)],
             card="shadow", m=(0, 0, 0, 0), sp=0, fixw=292)
    res = W("QScrollArea", "resScroll", kids=[W("QWidget", "resHost", lay="H", m=(0, 0, 6, 6), sp=14)], fixh=102)
    path = F("pathCard", [L("lblPath", "SAFE EXECUTION PATH", "eyebrow"), W("QWidget", "pathHost", lay="V", m=(0, 0, 0, 0), sp=0, minh=70),
                          L("lblWork", "Work: —", "eyebrow")], card="shadowaccent", m=(14, 12, 14, 12), sp=8)
    audit = F("audit", [C("auHead", [L("lblAudit", "RESOURCE AUDIT", "h3"), S(), B("btnAddProc", "+ Process", "mini"), B("btnDelProc", "− Process", "mini"),
                                     B("btnAddRes", "+ Resource", "mini"), B("btnDelRes", "− Resource", "mini"),
                                     L("lblVec", "A B C vectors", "eyebrow")], lay="H", sp=8),
                        W("QTableWidget", "tblAudit"), L("lblAuditNote", "Cells hold one number per resource, separated by spaces. Edit them freely.", "eyebrow")],
              card="shadow", m=(16, 12, 16, 10), sp=6)
    hdr = C("hdr", [title_block("SAFEHOUSE", "BANKER’S ALGORITHM / RESOURCE SECURITY"), S(),
                    F("badge", [L("lblState", "✓ SAFE STATE", "stat"), L("lblStateSub", "5 / 5 can finish", "small")], card="shadowaccent", m=(16, 6, 16, 6), sp=0, fixw=216, fixh=60)], lay="H")
    save("bankers_algorithm.ui", page([hdr, C("body", [left, C("right", [res, path, audit], sp=12, stretch="0,0,1")], lay="H", sp=16, stretch="0,1")]))


# ------------------------------------------------------------------ Paging
def paging():
    band = F("band", [title_block("PAGEPORT", "PAGING / ADDRESS TRANSLATOR"), S(),
                      C("addrBox", [L("lblAddr", "LOGICAL ADDRESS", "eyebrow"),
                                    C("addrRow", [W("QLineEdit", "edAddr", "", ph="e.g. 2172", fixw=200, fixh=38), W("QComboBox", "cmbPage", editable=True, fixw=190, fixh=38)], lay="H", sp=16)], sp=4),
                      B("btnTranslate", "Translate address →", "dark", fixw=278, fixh=40)],
             lay="H", card="band", m=(22, 12, 22, 12), sp=26, fixh=88)

    def step(i, tag, big, sub, accent=False):
        return F(f"step{i}", [L(f"lblTag{i}", tag, "eyebrow"), L(f"lbl{big[0]}", big[1], "big"), L(f"lbl{sub[0]}", sub[1], "muted")],
                 card="shadowaccent" if accent else "shadow", m=(16, 12, 16, 12), sp=8)
    steps = C("steps", [step(1, "01 / SPLIT", ("Page", "Page 2"), ("Offset", "Offset: 124 bytes")), L("arr1", "→", "arrow"),
                        step(2, "02 / LOOKUP", ("Frame", "Frame 5"), ("Entry", "Page table entry: valid")), L("arr2", "→", "arrow"),
                        step(3, "03 / RESOLVE", ("Phys", "5,244 B"), ("PhysSub", "Physical address"), True)], lay="H", sp=10, stretch="1,0,1,0,1")
    dirc = F("dirCard", [L("lblDir", "PAGE DIRECTORY", "eyebrow"), W("QTableWidget", "tblPages"),
                         C("pgBtns", [B("btnAddPage", "+ Page", "mini"), B("btnDelPage", "− Page", "mini"), S()], lay="H", sp=8),
                         L("lblNote", "", "small", wrap=True)], card="shadow", m=(14, 12, 14, 12), sp=6, fixw=335)
    ram = F("ramCard", [C("ramHead", [L("lblRam", "PHYSICAL RAM", "eyebrow"), S(), L("lblFrames", "FRAMES", "eyebrow"),
                                      W("QSpinBox", "spinFrames", rng=(1, 100000), val=6, fixw=78, fixh=28), L("lblRamInfo", "6 frames × 1,024 bytes", "eyebrow")], lay="H", sp=8),
                        W("QScrollArea", "ramScroll", kids=[W("QWidget", "ramHost", lay="G", m=(0, 0, 4, 4), sp=10)])], card="shadow", m=(14, 12, 14, 12), sp=6)
    resolved = F("resolved", [L("lblResTag", "ADDRESS RESOLVED / VALID", "eyebrow"), L("lblFormula", "5 × 1,024 + 124 = 5,244", "big2"),
                              L("lblFormula2", "Page = floor(2172 / 1024)      Offset = 2172 mod 1024", "small")], card="shadowaccent", m=(16, 12, 16, 12), sp=6, fixh=96)
    body = C("body", [dirc, C("rightCol", [ram, resolved], sp=12, stretch="1,0")], lay="H", sp=16, stretch="0,1")
    save("paging.ui", W("QWidget", "page", lay="V", m=(0, 0, 0, 0), sp=0, kids=[band, C("pad", [steps, body], m=(22, 12, 22, 8), sp=12, stretch="0,1")]))


# ------------------------------------------------------------------ Page replacement
def pagerep():
    hdr = C("hdr", [title_block("FRAMELOG", "PAGE REPLACEMENT / EVICTION LAB"), S(),
                    B("btnFIFO", "FIFO", "seg", checkable=True, excl=True, checked=True, fixw=126, fixh=38),
                    B("btnLRU", "LRU", "seg", checkable=True, excl=True, fixw=126, fixh=38),
                    B("btnOpt", "Optimal", "seg", checkable=True, excl=True, fixw=126, fixh=38),
                    B("btnReplay", "Replay →", "primary", fixw=150, fixh=38)], lay="H", sp=10)
    ref = F("refCard", [C("refCol", [L("lblRef", "REFERENCE STRING", "eyebrow"), W("QLineEdit", "edRefs", "", ph="e.g. 7, 0, 1, 2, 0, 3, 0, 4", dyn={"kind": "refs"})], sp=6),
                        S(), F("frameBox", [B("btnMinus", "−", "flat"), L("lblFrames", "3 FRAMES", "mono"), B("btnPlus", "+", "flat")],
                               lay="H", card="accentbox", m=(10, 4, 10, 4), sp=18, fixw=194, fixh=42)],
            lay="H", card="shadow", m=(16, 12, 16, 12), sp=10)
    hist = F("histCard", [C("hiHead", [L("lblHist", "FRAME HISTORY", "eyebrow"), S(), L("lblLegend", "F = fault   /   H = hit", "eyebrow")], lay="H"),
                          W("QScrollArea", "histScroll", kids=[W("QWidget", "histHost", lay="V", m=(0, 0, 0, 0), sp=0)]),
                          L("lblNote", "", "eyebrow")], card="shadow", m=(16, 12, 16, 10), sp=6)
    queue = F("queueCard", [L("lblQ", "RESIDENCE QUEUE / FINAL STATE", "eyebrow"),
                            C("qRow", [L("lblOldest", "OLDEST", "eyebrow"), W("QWidget", "queueHost", lay="H", m=(0, 0, 0, 0), sp=14), S(), L("lblNewest", "NEWEST", "eyebrow")], lay="H", sp=26)],
              card="accentbox2", m=(16, 12, 16, 12), sp=10, fixh=124)
    insp = F("inspector", [L("lblBand", "EVENT INSPECTOR", "band"),
                           C("inBody", [L("lblStep", "STEP 08 / 08", "eyebrow"), L("lblPageBig", "Page 4", "h1s"),
                                        F("faultBadge", [L("lblFault", "PAGE FAULT", "mono")], card="accentbox", m=(12, 6, 12, 6), fixh=34),
                                        L("lblEv", "Evicted page", "muted"), L("lblEvict", "2 → 4", "h2"), L("lblEvSub", "Frame 1 overwritten", "eyebrow"),
                                        L("lblFaults", "7", "h1s", dyn={"gap": "1"}), L("c1", "TOTAL FAULTS", "eyebrow"),
                                        L("lblHits", "1", "h1s"), L("c2", "TOTAL HITS", "eyebrow"),
                                        L("lblHitRatio", "12.5%", "h1s"), L("c3", "HIT RATIO", "eyebrow"),
                                        L("lblFaultRatio", "Fault ratio: 87.5%", "eyebrow"), S(True)], m=(16, 14, 16, 14), sp=4)],
             card="shadow", m=(0, 0, 0, 0), sp=0, fixw=232)
    body = C("body", [C("leftCol", [ref, hist, queue], sp=14, stretch="0,1,0"), insp], lay="H", sp=20, stretch="1,0")
    save("page_replacement.ui", page([hdr, body], sp=14))


# ------------------------------------------------------------------ Segmentation
def segmentation():
    band = F("band", [title_block("SEGMENT STUDIO", "SEGMENTATION / LOGICAL MEMORY EDITOR"), S(),
                      F("probeBox", [L("lblSegTag", "segment", "mono"), W("QComboBox", "cmbSeg", editable=True, fixw=72, fixh=30), L("colon", ":", "mono"),
                                     L("lblOffTag", "offset", "mono"), W("QLineEdit", "edOffset", "", ph="offset", fixw=96, fixh=30)],
                        lay="H", card="whitebox", m=(14, 6, 14, 6), sp=10, fixw=296, fixh=42),
                      B("btnProbe", "Probe →", "dark", fixw=138, fixh=42)], lay="H", card="band", m=(22, 12, 22, 12), sp=16, fixh=76)
    expl = F("explorer", [L("lblEx", "EXPLORER", "eyebrow"), W("QScrollArea", "segScroll", kids=[W("QWidget", "segHost", lay="V", m=(0, 0, 4, 4), sp=10)]),
                          B("btnAddSeg", "+ Add segment", "link")], card="shadow", m=(14, 12, 14, 12), sp=8, fixw=215)
    space = F("spaceCard", [L("lblSp", "PHYSICAL ADDRESS SPACE", "eyebrow"), L("lblRange", "0–6,800 bytes / gaps shown", "eyebrow"),
                            W("QWidget", "spaceHost", lay="V", m=(0, 0, 0, 0), sp=0, minh=300), L("lblGaps", "Gaps = unallocated address ranges", "eyebrow")],
              card="shadow", m=(16, 12, 16, 12), sp=6)
    insp = F("insp", [L("lblIn", "BOUNDS INSPECTOR", "eyebrow"), L("lblSegName", "0 / Code", "h1s"),
                      F("permBox", [L("lblPerms", "READ   /   EXECUTE", "mono")], card="accentbox", m=(14, 6, 14, 6), fixh=34),
                      L("t1", "Base address", "muted", dyn={"gap": "1"}), L("lblBase", "1,000 B", "h2"), L("t2", "Segment limit", "muted"), L("lblLimit", "600 B", "h2"),
                      L("t3", "Requested offset", "muted"), L("lblOffsetV", "240 B", "h2"),
                      F("verdict", [L("lblVerdict", "✓  240 < 600", "h2"), L("lblVerdictSub", "Offset is within bounds", "small")], card="accentbox", m=(14, 8, 14, 8), sp=0),
                      L("t4", "PHYSICAL ADDRESS", "eyebrow", dyn={"gap": "1"}), L("lblPhys", "1,240 B", "h1s"), L("lblPhysSub", "1,000 + 240 = 1,240", "eyebrow"), S(True)],
            card="shadow", m=(16, 12, 16, 12), sp=4, fixw=312)
    save("segmentation.ui", W("QWidget", "page", lay="V", m=(0, 0, 0, 0), sp=0, kids=[band, C("pad", [expl, space, insp], lay="H", m=(22, 16, 22, 8), sp=16, stretch="0,1,0")]))


# ------------------------------------------------------------------ Fragmentation
def fragmentation():
    hdr = C("hdr", [title_block("GAPSCAN", "FRAGMENTATION / PARTITION AUDIT"), S(),
                    B("btnInternal", "Internal", "seg", checkable=True, excl=True, checked=True, fixw=140, fixh=38),
                    B("btnExternal", "External", "seg", checkable=True, excl=True, fixw=140, fixh=38), L("gap1", "", None, fixw=20),
                    B("btnSetup", "Setup ✎", "plain", fixw=120, fixh=38), B("btnExport", "Export report ↗", "plain", fixw=180, fixh=38)], lay="H", sp=12)
    audit = F("auditCard", [L("lblAudit", "AUDIT NO. 004", "eyebrow"), L("lblMem", "Memory\nleft behind.", "h1m"), S(True), L("lblBig", "472", "huge"),
                            L("lblBigCap", "KB / INTERNAL WASTE", "eyebrow"), L("lblPct", "46.1% of allocated memory", "body"),
                            W("QFrame", "rule", dyn={"rule": "1"}, fixh=3),
                            W("QWidget", "sumGrid", lay="G", m=(0, 4, 0, 4), sp=8, kids=[
                                (L("sT", "TOTAL", "mono"), 0, 0), (L("lblTotal", "1,024 KB", "mono"), 0, 1),
                                (L("sU", "USED", "mono"), 1, 0), (L("lblUsed", "552 KB", "mono"), 1, 1),
                                (L("sE", "EXTERNAL", "mono"), 2, 0), (L("lblExt", "0 KB", "mono"), 2, 1)]),
                            S(True), F("cfgBox", [L("lblCfg", "4 × 256 KB / FIXED", "mono")], card="darkbox", m=(16, 12, 16, 12), fixh=46)],
              card="shadowaccent", m=(18, 16, 18, 16), sp=6, fixw=266)
    parts = W("QScrollArea", "partScroll", kids=[W("QWidget", "partHost", lay="G", m=(0, 0, 6, 6), sp=14)])
    eff = F("effCard", [C("effL", [L("lblEff", "MEMORY EFFICIENCY", "eyebrow"), W("QWidget", "effBarHost", lay="V", m=(0, 0, 0, 0), sp=0, fixh=22),
                                   C("effLbl", [L("lblEffUsed", "53.9% used", "boldmono"), S(), L("lblEffWaste", "46.1% wasted", "eyebrow")], lay="H")], sp=8),
                        C("effR", [L("lblWhyT", "Why not compact?", "h3"), L("lblWhy", "", "muted", wrap=True)], sp=4)],
              lay="H", card="shadow", m=(16, 12, 16, 12), sp=36, stretch="1,1", fixh=118)
    save("fragmentation.ui", page([hdr, C("body", [audit, C("right", [parts, eff], sp=14, stretch="1,0")], lay="H", sp=14, stretch="0,1")]))


# ------------------------------------------------------------------ Disk
def disk():
    hdr = C("hdr", [title_block("SEEK", "DISK SCHEDULING / ROUTE PLOTTER"), S()] +
            [B(f"btn{n}", t, "seg", checkable=True, excl=True, checked=(n == "FCFS"), fixw=118, fixh=38)
             for n, t in (("FCFS", "FCFS"), ("SSTF", "SSTF"), ("SCAN", "SCAN"), ("CSCAN", "C-SCAN"), ("LOOK", "LOOK"), ("CLOOK", "C-LOOK"))] +
            [L("gap1", "", None, fixw=10), B("btnTrace", "Trace disk head →", "primary", fixw=206, fixh=38)], lay="H", sp=10)
    plot = F("plotCard", [C("plHead", [L("lblPlot", "HEAD MOVEMENT / FCFS", "eyebrow"), S(), L("lblPlotRange", "53 start → 67 end", "eyebrow")], lay="H"),
                          W("QScrollArea", "plotScroll", kids=[W("QWidget", "plotHost", lay="V", m=(0, 0, 0, 0), sp=0)]),
                          L("lblAxes", "CYLINDER →      /      REQUEST ORDER ↓", "eyebrow")], card="shadow", m=(16, 12, 16, 12), sp=6)
    led = F("ledgerCard", [L("lblBand", "REQUEST LEDGER", "band"),
                           C("ldBody", [W("QTableWidget", "tblLedger"),
                                        C("hr", [C("hs", [L("h1", "HEAD START", "eyebrow"), L("lblHead", "53", "h2")], sp=0), C("rg", [L("h2", "RANGE", "eyebrow"), L("lblRange", "0–199", "h2")], sp=0), S()], lay="H", sp=30),
                                        B("btnEdit", "+ Edit request queue", "primary", fixh=38)], m=(14, 10, 14, 12), sp=8)],
             card="shadow", m=(0, 0, 0, 0), sp=0, fixw=270)
    stats = F("statsBar", [C("s1", [L("lblMoved", "640", "huge2"), L("c1", "CYLINDERS MOVED", "eyebrow")], sp=2),
                           C("s2", [L("lblAvg", "80.0", "huge2"), L("c2", "AVG SEEK / REQUEST", "eyebrow")], sp=2),
                           C("s3", [L("lblServed", "8 / 8", "huge2"), L("c3", "REQUESTS SERVICED", "eyebrow")], sp=2)],
              lay="H", card="shadowaccent", m=(16, 10, 16, 10), sp=20, stretch="1,1,1", fixh=88)
    save("disk_scheduling.ui", page([hdr, C("body", [plot, led], lay="H", sp=20, stretch="1,0"), stats], sp=14))


# ------------------------------------------------------------------ Multiprogramming
def multi():
    hdr = C("hdr", [title_block("RESIDENT", "MULTIPROGRAMMING / CAPACITY PLANNER"), S(),
                    B("btnSystem", "512 / 1,024 MB\n50% memory occupied", "memory", fixw=380, fixh=56)], lay="H")
    cards = W("QScrollArea", "cardsScroll", kids=[W("QWidget", "cardsHost", lay="H", m=(0, 0, 6, 8), sp=16)], fixh=132)
    chart = F("chartCard", [C("chHead", [L("lblChart", "MORE PROGRAMS, LESS IDLE TIME", "eyebrow"), S(),
                                         B("btnModel", "Model", "mini", checkable=True, excl=True, checked=True), B("btnSim", "Simulation", "mini", checkable=True, excl=True),
                                         L("lblP", "p = 0.8", "eyebrow")], lay="H", sp=8),
                            W("QStackedWidget", "stack", kids=[
                                W("QWidget", "curveHost", lay="V", m=(0, 0, 0, 0), sp=0),
                                W("QWidget", "simPage", lay="V", m=(0, 0, 0, 0), sp=6, kids=[
                                    W("QWidget", "simHost", lay="V", m=(0, 0, 0, 0), sp=0, minh=120),
                                    C("simCtl", [B("btnRunSim", "Run simulation", "mini"), W("QSlider", "sliderTick", orient="Horizontal"), L("lblTick", "tick 0", "eyebrow")], lay="H", sp=10),
                                    L("lblSimStats", "", "small", wrap=True)])])],
              card="shadow", m=(16, 12, 16, 10), sp=6)
    what = F("whatIf", [L("lblWI", "WHAT-IF CONSOLE", "eyebrow"), L("lblU", "59.04%", "huge"), L("lblUCap", "Expected CPU utilization", "body"),
                        L("lblDeg", "DEGREE / n", "eyebrow", dyn={"gap": "1"}),
                        F("degBox", [B("btnNm", "−", "flat"), L("lblN", "4", "mono"), B("btnNp", "+", "flat")], lay="H", card="darkline", m=(14, 4, 14, 4), sp=0, fixh=40),
                        L("lblPW", "I/O WAIT PROBABILITY / p", "eyebrow", dyn={"gap": "1"}),
                        W("QSlider", "sliderP", orient="Horizontal", rng=(0, 100), val=80),
                        C("pRow", [L("z0", "0%", "eyebrow"), S(), L("lblPv", "80%", "boldmono"), S(), L("z1", "100%", "eyebrow")], lay="H"),
                        S(True), L("lblAssume", "Assumes independent I/O waits.", "small")], card="shadowaccent", m=(16, 14, 16, 14), sp=6, fixw=318)
    model = F("modelCard", [L("lblModelT", "THE MODEL", "eyebrow"), L("lblModel", "U = 1 − pⁿ = 1 − 0.8⁴ = 59.04%", "big2")], card="shadow", m=(16, 10, 16, 10), sp=4, fixh=84)
    save("multiprogramming.ui", page([hdr, cards, C("mid", [C("midL", [chart, model], sp=12, stretch="1,0"), what], lay="H", sp=20, stretch="1,0")], sp=12))


# ------------------------------------------------------------------ Windows-XP style desktop (skin 2)
def xp_desktop():
    task = F("xpTaskbar", [B("btnStartXP", "start", "xpstart", fixw=146, fixh=40),
                           B("btnQL1", "", "xpql", fixw=30, fixh=30), B("btnQL2", "", "xpql", fixw=30, fixh=30),
                           W("QFrame", "qlSep", dyn={"xpsep": "1"}, fixw=2, fixh=28),
                           W("QWidget", "taskButtons", lay="H", m=(0, 0, 0, 0), sp=4),
                           S(), L("lblNote", "Welcome to your little OS lab.", "xpnote"),
                           F("xpTray", [L("lblSound", "♪", "xptray"), L("lblNet", "◉", "xptray"), L("lblClock", "09:41 AM", "xptray")],
                             lay="H", m=(14, 0, 18, 0), sp=14, fixh=40)],
             lay="H", m=(0, 0, 0, 0), sp=6, fixh=40)
    save("xp_desktop.ui", W("QWidget", "XPDesktop", lay="V", m=(0, 0, 0, 0), sp=0, stretch="1,0",
                            kids=[W("QWidget", "deskHost", lay="V", m=(0, 0, 0, 0), sp=0), task]))


def xp_window():
    title = F("xpTitle", [L("lblIcon", "", "xpicon", fixw=20, fixh=20), L("lblTitle", "My OS Lab", "xptitle"), S(),
                          B("btnMin", "−", "xpwin", fixw=22, fixh=22), B("btnMax", "▢", "xpwin", fixw=22, fixh=22),
                          B("btnClose", "✕", "xpclose", fixw=22, fixh=22)], lay="H", m=(8, 0, 6, 0), sp=3, fixh=30)
    menu = F("xpMenu", [W("QWidget", "menuHost", lay="H", m=(0, 0, 0, 0), sp=2), S()], lay="H", m=(6, 0, 6, 0), sp=0, fixh=24)
    status = F("xpStatus", [L("lblStatus", "", "xpstatus"), S(), L("lblStatusR", "", "xpstatus")], lay="H", m=(8, 0, 22, 0), sp=0, fixh=22)
    save("xp_window.ui", W("QWidget", "xpRoot", lay="V", m=(0, 0, 0, 0), sp=0, kids=[title, menu, W("QWidget", "bodyHost", lay="V", m=(0, 0, 0, 0), sp=0), status], stretch="0,0,1,0"))


def xp_explorer():
    tool = F("xpToolbar", [B("btnBack", "◀  Back", "xptool"), B("btnForward", "Forward  ▶", "xptool"), B("btnUp", "▲", "xptool"),
                           W("QFrame", "tSep1", dyn={"xpsep": "1"}, fixw=2, fixh=24), B("btnSearch", "Search", "xptool"),
                           B("btnFolders", "Folders", "xptool"), W("QFrame", "tSep2", dyn={"xpsep": "1"}, fixw=2, fixh=24),
                           B("btnViews", "Views ▾", "xptool"), S()], lay="H", m=(8, 4, 8, 4), sp=6, fixh=40)
    addr = F("xpAddress", [L("lblAddr", "Address", "xpmuted"), W("QLineEdit", "edAddr", "C:\\Kernel\\Applications", fixh=24),
                           B("btnGo", "Go  →", "xptool")], lay="H", m=(8, 3, 8, 3), sp=8, fixh=32)

    def box(name, head, kids):
        return F(name, [B(name + "Head", head, "xphead")] + kids, card=None, m=(0, 0, 0, 8), sp=2, dyn={"xp": "box"})
    links = lambda items: [B(n, t, "xplink") for n, t in items]
    pane = W("QWidget", "xpPane", lay="V", m=(12, 14, 12, 12), sp=12, fixw=214, kids=[
        box("boxTasks", "System tasks", links([("lnkRun", "›  Run a simulation"), ("lnkWall", "›  Change wallpaper"), ("lnkExport", "›  Export results")])),
        box("boxPlaces", "Other places", links([("lnkComputer", "My Computer"), ("lnkDocs", "My Documents"), ("lnkPanel", "Control Panel")])),
        box("boxDetails", "Details", [L("lblD1", "My OS Lab", "xpbold"), L("lblD2", "8 applications", "xpsmall"), L("lblD3", "Operating systems toolkit", "xpsmall"),
                                      L("lblD4", "All programs run locally.\nReady when you are.", "xpsmall")]), S(True)])
    content = W("QWidget", "xpContent", lay="V", m=(24, 20, 24, 14), sp=8, kids=[
        L("lblWelcome", "Welcome back, Student.", "xph1"),
        L("lblWelcomeSub", "Your little OS lab. Eight big concepts, one familiar desktop.", "xpmuted"),
        C("appsHdr", [L("lblApplications", "Applications", "xph2"), S(), L("lblHint", "Double-click an icon to open", "xpsmall")], lay="H"),
        W("QFrame", "xpRule", dyn={"xprule": "1"}, fixh=1),
        W("QWidget", "gridHost", lay="G", m=(0, 8, 0, 0), sp=14), S(True),
        F("xpTip", [L("lblTip", "Tip: Start with Dispatch to explore how processes take turns on the CPU.", "xpsmall")], lay="H", m=(12, 8, 12, 8), dyn={"xp": "tip"})])
    save("xp_explorer.ui", W("QWidget", "page", lay="V", m=(0, 0, 0, 0), sp=0, stretch="0,0,1",
                             kids=[tool, addr, C("xpBody", [pane, content], lay="H", sp=0, stretch="0,1")]))


if __name__ == "__main__":
    for f in (xp_desktop, xp_window, xp_explorer, main_window, home, settings, cpu, bankers, paging, pagerep, segmentation, fragmentation, disk, multi):
        f()
    print("ui files written:", sorted(os.listdir("ui")))
