# Kernel — Operating System Simulator
An offline desktop lab with eight Operating Systems simulators, built with **Python + PySide6** and recreated from the supplied Figma export.
It ships with **two desktops** that host the same neo-brutalist simulators:
* **Kernel XP (default)** — Windows-XP-style desktop: changeable wallpaper (right-click the desktop → *Change Wallpaper…*: 6 built-in sharp wallpapers **or your own real pictures** — *Add pictures…* (several at once, remembered in the list, *Remove* to forget one), drop files into the `wallpapers/` folder, or just **drag an image file onto the desktop**; position Fill / Fit / Stretch / Center / Tile), desktop shortcuts for **all 8 apps** (drag to rearrange, snap to grid, *Arrange Icons* in the context menu), a "My OS Lab" explorer window, a Start menu, a task bar with
  window buttons and clock, and draggable / resizable / minimisable XP windows (several simulators can be open at once).
* **Kernel / 98** — the teal retro desktop (light + dark). Switch with *Start → All Programs → Kernel / 98 desktop* (or XP *Tools* menu); back via *View → Switch to Windows XP desktop*.

`python main.py` opens the last-used desktop (XP the first time); `python main.py --skin 98` forces Kernel / 98.

| # | App (window title) | Module | Algorithms |
|---|---|---|---|
| 1 | Dispatch | CPU scheduling | FCFS, SJF / SRTF, Priority (non-preemptive & preemptive), Round Robin; Gantt chart, ledger, averages, policy comparison (Matplotlib) |
| 2 | Safehouse | Banker's algorithm | Need matrix, safety algorithm, safe sequence, resource-request sandbox |
| 3 | Pageport | Paging | page table, logical→physical translation, valid / invalid / page-fault handling, frame map |
| 4 | Framelog | Page replacement | FIFO, LRU, Optimal; frame-by-frame history, hits/faults/ratios |
| 5 | Segment Studio | Segmentation | segment table, base+limit protection, physical memory map with gaps |
| 6 | Gapscan | Fragmentation | first / best / worst / next fit, fixed and dynamic partitions, internal & external fragmentation |
| 7 | Seek | Disk scheduling | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK, direction + disk limits |
| 8 | Resident | Multiprogramming | U = 1 − pⁿ model + seeded tick simulation (memory, resource units, running/ready/I-O-wait/queued/done) |

## Documentation
| Document | Contents |
|---|---|
| **docs/SETUP.md** | required libraries and versions, install, run, tests, Qt Designer, troubleshooting |
| **docs/MODULES.md** | every module: purpose, inputs (incl. fast text entry), outputs, algorithm steps, formulas, validation, complexity, files |
| docs/ALGORITHMS.md | one-page algorithm summary |
| samples/ | reference cases checked by the tests (nothing is pre-loaded in the apps) |

## Commands (Windows / PyCharm terminal)
```
pip install -r requirements.txt          # 1. install dependencies
pyside6-designer ui\cpu_scheduling.ui     # 2. open any .ui file in Qt Designer (ui\*.ui)
pyside6-uic ui\cpu_scheduling.ui -o gui\ui_cpu_scheduling.py   # 3. (optional) generate Python from a .ui
python main.py                           # 4. run the application
python -m pytest -q                      # 5. run the tests (104)
```
In PyCharm: open the folder, set the interpreter that has the requirements, right-click `main.py` → Run.

## Qt Designer workflow
All screens live in `ui/*.ui`. The app loads them at runtime with `QUiLoader`, so **edit in Designer, save, run `python main.py`** — no regeneration step is
needed and hand-written logic is never overwritten. Logic finds widgets by `objectName` (e.g. `btnRun`, `tblLedger`), so keep those names when editing.
Dynamic/custom-painted parts (Gantt, frame history, disk plot, memory map, curve, cards) are inserted into named placeholder containers (`ganttHost`, …).
`tools/make_ui.py` is the script that originally generated the `.ui` files; **do not re-run it after editing in Designer** (it overwrites them).
Colours come from `gui/theme.py` (QSS is built from palettes sampled from the Figma file; reference copies are in `gui/styles/*.qss`).

## Project layout
```
main.py            entry point                      algorithms/   pure-Python OS algorithms (no Qt)
ui/                Qt Designer .ui files            models/       dataclasses shared by algorithms and GUI
gui/main_window.py Kernel / 98 desktop shell        
gui/xp_desktop.py  Windows-XP desktop (xp_theme.py = its QSS)    utils/        validators + helpers
gui/pages/         one class per simulator           tests/        pytest suites (8 algorithm suites + GUI smoke test)
gui/widgets/       custom painted widgets            samples/      sample inputs + expected outputs
gui/theme.py       palettes + QSS                    assets/       icons (extracted from the Figma PDF), fonts (Inter, JetBrains Mono)
tools/             make_ui.py, extract_icons.py, screenshots.py
```

## Algorithm documentation
See `docs/ALGORITHMS.md` for a plain-language summary of every algorithm. The source in `algorithms/` carries a docstring on every function and a comment on every logical block.

## Fast input
Where typing one row at a time would be slow, every app offers a whole-table text box (spaces / commas / tabs / Excel paste): CPU scheduling *Edit as text…* (+ Enter-key row entry), Banker's *Enter matrices…*,
Paging *Edit as text…*, Segmentation *Edit as text…*, Multiprogramming *Paste list…*. Page replacement, Fragmentation and Disk scheduling already take a whole list in one box. Formats are in docs/MODULES.md.

## Windows never cut off content
Each app opens large enough to show everything; if you shrink the window, scroll bars appear instead of clipping.

## Behaviour notes / conventions
* **No fixed limits**: processes, resources, frames, page-table rows, segments, blocks, requests and programs are unlimited (add/remove buttons, comma lists, scrolling).
* **Validation**: empty, non-numeric, negative, out-of-range, duplicate, inconsistent input shows a message instead of crashing (`utils/validators.py`, `@safe` slot decorator).
* CPU: lower priority number = higher priority; ties → earlier arrival → input order; RR queues new arrivals before the pre-empted process; CPU-busy % and throughput use the span from first arrival to last completion.
* Banker's: safety scan passes over P0…Pn-1 in order (gives the same sequence as the design: P1 P3 P4 P0 P2).
* Paging: pages beyond the table = invalid address; valid flag "No" = page fault. Frames must exist and be unique.
* Page replacement: a page takes its victim's frame slot; Optimal ties → lowest frame slot.
* Disk: SCAN/C-SCAN always sweep to the disk edge, LOOK/C-LOOK stop at the last request; C-SCAN/C-LOOK return jumps are counted (toggle in "Edit request queue").
* Fragmentation: "external" = free memory that exists in total but cannot host a waiting process because it is split into holes.
* Multiprogramming: each resident program is blocked on I/O in a tick with its own probability (seeded RNG → reproducible); one ready program runs per tick.
* Settings: theme (live), accent colour, UI sounds, reduced motion, playback speed (affects Play / Replay), learning tips (hides the tip bar in My OS Lab); saved with *Save preferences* (QSettings).

## Clean start
Every simulator opens **empty** — no sample data is built into any app. You type your own processes, matrices, page tables, reference strings, segments, memory blocks, disk requests or programs.
(`samples/` only documents the textbook cases that the automated tests check; nothing is loaded from it.)

## Performance notes
* Card shadows are plain solid frames kept in sync with the cards (no `QGraphicsDropShadowEffect`, which re-renders every card and its children on each repaint).
* XP stylesheets are scoped to the task bar / window chrome / explorer / Start menu instead of cascading over the simulators; there is no application-wide event filter any more (the Start menu is a native popup).
* The wallpaper is painted once into a cached pixmap (rebuilt ~120 ms after a resize settles); the clock only repaints when the minute changes.
* `python tools/bench.py` prints rough repaint / window-drag timings (offscreen). On the dev machine a window-drag step went from ~89 ms to ~14 ms.

## My OS Lab
*My OS Lab* is the folder window of the eight applications (address bar, search, views). *My Computer* was removed from the XP desktop as redundant (it only exists on the Kernel / 98 desktop as its home screen). The Control Panel icon is no longer on the desktop; it is in the Start menu.

## XP desktop features (all functional)
Desktop shortcuts (double-click, drag, right-click → Open), desktop context menu, My OS Lab explorer (Back / Forward / Up history, Address bar — try `C:\Kernel\Applications\Seek`, Search filter, Views large/small icons,
Folders pane toggle, System tasks links, Other places), Start menu (apps, My OS Lab/Documents, Control Panel, Run…, Search, Help, All Programs, Log off, Turn off),
task-bar buttons (click to restore/minimise), quick-launch icons, clock. *Control Panel* (Start menu / quick-launch) opens Settings.

## Known limitations
* XP desktop: no Recycle Bin / My Documents browser (My Documents opens your Documents folder in the OS file manager); the XP "Control Panel" is the same Settings screen as Kernel / 98; the
  desktop theme (Light/Dark) only changes the simulators, the XP chrome always stays XP blue.
* XP icons were extracted from the PDF (raster). Wallpaper choice applies to the Kernel XP desktop only (Kernel / 98 keeps its teal desktop).
* Desktop icons use the artwork extracted from the PDF (raster, 128 px), not original vector sources.
* Matplotlib is used for the *Compare policies* chart; the other visualisations are custom Qt painting for pixel fidelity.
* Window minimise/close both hide the window to the taskbar; there is a single application window.
* Visual match was checked by rendering each page and comparing it with the PDF; it is close but not pixel-identical (fonts/anti-aliasing differ).
