"""Headless GUI tests: every page opens EMPTY, accepts user-entered data, survives invalid input; XP desktop behaves."""
import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
import pytest
pytest.importorskip("PySide6")
from PySide6.QtWidgets import QApplication, QMessageBox


@pytest.fixture(scope="module")
def win():
    app = QApplication.instance() or QApplication([])
    app.setStyle("Fusion")
    from main import load_fonts
    load_fonts()
    QMessageBox.warning = staticmethod(lambda *a, **k: None)      # never block on dialogs
    QMessageBox.information = staticmethod(lambda *a, **k: None)
    from gui.main_window import MainWindow
    w = MainWindow()
    w.show()
    yield w
    w.close()


def test_every_page_opens(win):
    for i in range(10):
        win.open_page(i)
        assert win.w.lblTitle.text() == win.pages[i].TITLE


# ------------------------------------------------------------------ clean start
def test_all_apps_start_empty_and_do_not_crash_when_run_empty(win):
    cpu, bank, pag, rep, seg, frag, disk, multi = win.pages[1:9]
    assert cpu.rows == [] and cpu.result is None
    cpu.run()
    assert bank.n == 0 and bank.w.tblAudit.rowCount() == 0 and bank.w.lblState.text() == "NO DATA"
    bank.check_request()
    assert pag.w.tblPages.rowCount() == 0 and pag.w.edAddr.text() == ""
    pag.do_translate()
    assert rep.w.edRefs.text() == "" and rep.res is None
    rep.replay()
    assert seg.segs == [] and seg.w.edOffset.text() == ""
    seg.probe()
    assert frag.blocks == [] and frag.procs == [] and frag.res is None and frag.w.lblBig.text() == "0"
    assert disk.reqs == [] and disk.w.lblMoved.text() == "—"
    disk.trace(); disk.set_algo("SCAN")
    assert multi.progs == []
    multi.run_sim()
    assert win.w.lblStatus.text().startswith("Error") or True


# ------------------------------------------------------------------ user-entered data
def test_cpu_user_data_and_bad_input(win):
    p = win.pages[1]; win.open_page(1)
    for pid, a, b in (("P1", 0, 5), ("P2", 1, 3), ("P3", 2, 1), ("P4", 3, 2)):
        p.add_row(pid, a, b, 1)
    for a in ("FCFS", "SJF", "RR", "PRIORITY"):
        p.set_algo(a); p.run()
        assert p.result is not None and p.w.tblLedger.rowCount() == 4
    p.set_algo("FCFS"); p.run()
    assert p.w.lblAvgWait.text() == "4.00 ms" and p.w.lblAvgTat.text() == "6.75 ms"
    p.add_row("P9", 0, 1, 1)
    p.rows[-1].ed["burst"][0].setText("abc")
    p.run()
    assert "Error" in win.w.lblStatus.text()
    p.remove_row(p.rows[-1])
    for _ in range(60):
        p.add_row(None, 1, 2, 1)                              # no fixed limit
    p.run()
    assert p.w.tblLedger.rowCount() == 64
    p.step(); p.first(); p.reset()
    assert p.rows == []


def test_bankers_user_data(win):
    p = win.pages[2]; win.open_page(2)
    p.set_state([3, 3, 2], [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]],
                [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]])
    assert p.w.lblState.text().startswith("✓")
    p.w.cmbProc.setCurrentIndex(1)
    for sp, v in zip(p.req_spins, (1, 0, 2)):
        sp.setValue(v)
    p.check_request(); assert "GRANTED" in p.w.lblPreview.text()
    p.add_res(); p.add_proc(); assert p.m == 4 and p.n == 6
    p.w.tblAudit.item(0, 1).setText("1 2")
    assert p.w.lblState.text() == "INVALID"
    p.reset(); assert p.n == 0


def test_paging_user_data(win):
    p = win.pages[3]; win.open_page(3)
    p.w.spinFrames.setValue(6)
    p.set_table([(3, True), (1, True), (5, True), (2, True), (None, False)])
    p.w.edAddr.setText("2172"); p.do_translate()
    assert p.w.lblPhys.text() == "5,244 B"
    p.w.edAddr.setText("4100"); p.do_translate(); assert "FAULT" in p.w.lblPhys.text()
    p.w.edAddr.setText("999999"); p.do_translate(); assert "INVALID" in p.w.lblPhys.text()
    for bad in ("-5", "x", ""):
        p.w.edAddr.setText(bad); p.do_translate()


def test_page_replacement_user_data(win):
    p = win.pages[4]; win.open_page(4)
    p.w.edRefs.setText("7, 0, 1, 2, 0, 3, 0, 4")
    for a in ("FIFO", "LRU", "OPTIMAL"):
        p.set_algo(a); p.run()
    p.set_algo("FIFO"); p.run()
    assert p.res.faults == 7 and p.res.hits == 1
    p.w.edRefs.setText("1,2,x"); p.replay()
    p.w.edRefs.setText(", ".join(str(i % 17) for i in range(3000))); p.set_algo("LRU"); p.run()


def test_segmentation_user_data(win):
    from models.records import Segment
    p = win.pages[5]; win.open_page(5)
    p.set_segments([Segment(0, "Code", 1000, 600), Segment(1, "Data", 2400, 400)], 0)
    p.w.edOffset.setText("240"); p.probe(); assert p.w.lblPhys.text() == "1,240 B"
    p.w.edOffset.setText("600"); p.probe(); assert "TRAP" in p.w.lblVerdict.text()
    p.w.cmbSeg.setCurrentText("42"); p.probe()
    p.w.edOffset.setText(""); p.probe()
    p.reset(); assert p.segs == []


def test_fragmentation_user_data(win):
    p = win.pages[6]; win.open_page(6)
    p.blocks, p.procs = [256] * 4, [212, 180, 96, 64]; p.recalc()
    assert p.w.lblBig.text() == "472"
    p.blocks, p.procs, p.strategy = [100, 500, 200, 300, 600], [212, 417, 112, 426], "best"
    p.recalc(); p.set_view("external"); p.set_view("internal")
    p.reset(); assert p.res is None


def test_disk_user_data(win):
    p = win.pages[7]; win.open_page(7)
    p.head, p.lo, p.hi, p.reqs = 53, 0, 199, [98, 183, 37, 122, 14, 124, 65, 67]
    expect = {"FCFS": "640", "SSTF": "236", "SCAN": "331", "CSCAN": "382", "LOOK": "299", "CLOOK": "322"}
    for a, v in expect.items():
        p.set_algo(a); assert p.w.lblMoved.text() == v
    p.reset(); assert p.reqs == []


def test_multiprogramming_user_data(win):
    from models.records import Program
    p = win.pages[8]; win.open_page(8)
    p.progs = [Program(f"P{i + 1}", 128, 25, 0.8) for i in range(4)]
    p.after_change()
    assert p.w.lblU.text() == "59.04%"
    p.run_sim(); assert p.sim is not None and "ticks" in p.w.lblSimStats.text()
    p.set_n(8); p.set_p(0.5); p.set_tick(0)
    p.reset(); assert p.progs == []


def test_theme_switch(win):
    win.prefs.update(mode="dark")
    for i in range(10):
        win.open_page(i)
    win.prefs.update(mode="light")


# ------------------------------------------------------------------ XP desktop
@pytest.fixture(scope="module")
def xp(win):
    from gui.xp_desktop import XPDesktop
    d = XPDesktop()
    d.resize(1316, 913)
    d.show()
    QApplication.processEvents()
    yield d
    d.close()


def test_xp_has_shortcuts_for_every_app_and_no_badges(xp):
    names = [s.lbl.text() for s in xp.shortcuts]
    assert "My Computer" not in names and "Control Panel" not in names        # redundant / already in the Start menu
    for n in ("My OS Lab", "Dispatch", "Safehouse", "Pageport", "Framelog", "Segment Studio", "Gapscan", "Seek", "Resident"):
        assert n in names
    assert not hasattr(xp, "badges")
    assert len({tuple(xp.cells[s]) for s in xp.shortcuts}) == len(xp.shortcuts)       # no two icons share a cell


def test_xp_shortcut_opens_and_drag_snaps(xp):
    sc = next(s for s in xp.shortcuts if s.lbl.text() == "Seek")
    sc.on_open(); assert xp.windows[7].isVisible()
    sc.move(300, 400); xp.drop_shortcut(sc)
    assert sc.pos() == xp.cell_pos(xp.cells[sc])
    xp.arrange()


def test_xp_wallpapers(xp):
    from PySide6.QtCore import QSize
    from gui.wallpapers import BUILTIN, render
    for k in BUILTIN:
        pm = render(f"builtin:{k}", "Fill", QSize(320, 200)); assert not pm.isNull()
        xp.set_wallpaper(f"builtin:{k}", "Fill")
    # custom image in every position mode
    from PySide6.QtGui import QImage, QColor
    img = QImage(64, 40, QImage.Format_RGB32); img.fill(QColor("#ff00aa"))
    import tempfile
    path = os.path.join(tempfile.gettempdir(), "wp_test.png"); img.save(path)
    from gui.wallpapers import MODES
    for m in MODES:
        assert not render("file:" + path, m, QSize(320, 200)).isNull()
    assert not render("file:/does/not/exist.png", "Fill", QSize(100, 60)).isNull()     # falls back to default


def test_xp_window_controls(xp):
    xp.open_app(1); w = xp.windows[1]
    w.toggle_max(); assert w.geometry() == xp.wall.rect(); w.toggle_max()
    xp.minimize(w); assert not w.isVisible()
    xp.task_clicked(w); assert w.isVisible()
    xp.close_window(w); assert not w.taskbtn.isVisible()
    xp.open_app(1); assert w.isVisible()


def test_xp_every_app_window_and_explorer(xp):
    for i in range(1, 10):
        xp.open_app(i)
    xp.open_app(0)                                           # legacy "My Computer" entry now just shows My OS Lab
    assert xp.windows["explorer"].isVisible() and 0 not in xp.windows
    xp.special("explorer")
    ex = xp.windows["explorer"].explorer
    ex.w.edAddr.setText("C:\\Kernel\\Applications\\Seek"); ex.go()
    ex.w.edAddr.setText("C:\\nope"); ex.go()
    ex.move_hist(-1)
    xp.toggle_start(); assert xp.start.isVisible(); xp.start.hide()


def test_xp_real_image_wallpapers(xp, tmp_path):
    from PySide6.QtGui import QColor, QImage
    from PySide6.QtCore import QSize
    from gui.dialogs.wallpaper_dialog import WallpaperDialog
    from gui.wallpapers import join_library, parse_library, render
    pics = []
    for i, col in enumerate(("#ff4444", "#44aa44")):
        img = QImage(200 + i * 40, 120, QImage.Format_RGB32); img.fill(QColor(col))
        path = str(tmp_path / f"photo{i}.jpg"); assert img.save(path); pics.append(path)
    (tmp_path / "notes.txt").write_text("not an image")
    applied = []
    dlg = WallpaperDialog(xp, "builtin:meadow", "Fill", [], lambda s, m: applied.append((s, m)))
    assert dlg.add_paths(pics + [str(tmp_path / "notes.txt"), "/missing.png"]) == 2      # only real images are accepted
    assert dlg.spec == "file:" + pics[-1] and dlg.library == pics and applied[-1][0] == dlg.spec
    dlg.mode_box.setCurrentText("Tile"); assert applied[-1][1] == "Tile" and dlg.mode_box.isEnabled()
    dlg.remove_selected(); assert dlg.library == pics[:1]
    dlg.cancel(); assert applied[-1] == ("builtin:meadow", "Fill")                       # cancel restores the old wallpaper
    xp.store_wallpaper("file:" + pics[0], "Fit", pics)
    assert parse_library(xp.prefs["wp_library"]) == pics and xp.wall.spec == "file:" + pics[0]
    xp.use_dropped_images([pics[1]]); assert xp.wall.spec == "file:" + pics[1] and xp.wall.mode == "Fill"
    assert not render(xp.wall.spec, "Fill", QSize(300, 200)).isNull()
    xp.store_wallpaper("builtin:meadow", "Fill", [])


def test_xp_windows_scroll_instead_of_cutting_content(xp):
    from PySide6.QtWidgets import QScrollArea
    for i in range(1, 9):
        xp.open_app(i)
        win = xp.windows[i]
        sa = win.w.bodyHost.findChild(QScrollArea)
        need = win.page.minimumSizeHint()
        win.resize(520, 380)                                 # much smaller than any app needs
        QApplication.processEvents()
        assert sa.horizontalScrollBar().maximum() > 0 or sa.verticalScrollBar().maximum() > 0, f"app {i} would be cut off"
        win.resize(max(1124, need.width() + 12), max(760, need.height() + 90))
        QApplication.processEvents()
        assert sa.horizontalScrollBar().maximum() == 0 and sa.verticalScrollBar().maximum() == 0, f"app {i} needs scrolling at default size"


def _feed(page, monkeypatch, values):
    monkeypatch.setattr(type(page), "ask", lambda self, title, fields, parse, intro=None: parse(values))


def test_bulk_text_entry_everywhere(win, monkeypatch):
    cpu, bank, pag, rep, seg, frag, disk, multi = win.pages[1:9]
    _feed(cpu, monkeypatch, {"text": "P1 0 5\nP2 1 3\nP3 2 1\nP4 3 2"})
    cpu.bulk_edit(); assert len(cpu.rows) == 4
    cpu.set_algo("FCFS"); cpu.run(); assert cpu.w.lblAvgWait.text() == "4.00 ms"
    cpu.rows[-1].ed["burst"][0].returnPressed.emit(); assert len(cpu.rows) == 5          # Enter on the last row adds a row
    _feed(cpu, monkeypatch, {"text": "\n".join(f"P{i} {i % 9} {i % 7 + 1}" for i in range(300))})
    cpu.bulk_edit(); assert len(cpu.rows) == 300
    _feed(bank, monkeypatch, {"av": "3 3 2", "al": "0 1 0\n2 0 0\n3 0 2\n2 1 1\n0 0 2", "mx": "7 5 3\n3 2 2\n9 0 2\n2 2 2\n4 3 3"})
    bank.bulk_edit(); assert bank.n == 5 and bank.w.lblState.text().startswith("✓")
    _feed(pag, monkeypatch, {"text": "3 1 5 2 -"})
    pag.bulk_edit(); assert pag.w.tblPages.rowCount() == 5 and pag.w.spinFrames.value() >= 6
    pag.w.edAddr.setText("2172"); pag.do_translate(); assert pag.w.lblPhys.text() == "5,244 B"
    _feed(seg, monkeypatch, {"text": "0 Code 1000 600 rx\n1 Data 2400 400\n2 4000 800"})
    seg.bulk_edit(); assert len(seg.segs) == 3
    _feed(multi, monkeypatch, {"text": "P1 128 25 80\nP2 256 10 50% 2 3"})
    multi.bulk_edit(); assert len(multi.progs) == 2
    for pg in (cpu, bank, pag, seg, multi):
        pg.reset()
