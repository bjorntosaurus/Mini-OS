# Setup and run instructions

## 1. Requirements
| Item | Version | Why |
|---|---|---|
| Python | 3.9 or newer (developed and tested on 3.12) | language |
| PySide6 | 6.6+ (tested 6.12.0) | Qt 6 GUI, `QUiLoader`, **Qt Designer** (`pyside6-designer`) and `pyside6-uic` |
| matplotlib | 3.7+ (tested 3.11.2) | the *Compare policies* chart in CPU scheduling (the rest of the app does not need it) |
| pytest | 7+ (tested 9.2.0) | running the automated tests |
| pymupdf, pillow, numpy | optional | only `tools/extract_icons.py` (re-extract artwork from the Figma PDF) |

Everything else (fonts Inter and JetBrains Mono, icons, `.ui` files, stylesheets) is bundled in the project. No internet connection is needed to run it.

## 2. Install (Windows / PyCharm — the intended workflow)
1. Unzip `OperatingSystemSimulator.zip` anywhere and open the folder in **PyCharm** (*File → Open*).
2. *File → Settings → Project → Python Interpreter → Add Interpreter → Add Local Interpreter → Virtualenv Environment → OK* (creates `.venv`).
3. Open the PyCharm **Terminal** (it activates the venv automatically) and run:
   ```
   pip install -r requirements.txt
   ```
Without PyCharm (PowerShell / cmd):
```
cd OperatingSystemSimulator
python -m venv .venv
.venv\\Scripts\\activate
pip install -r requirements.txt
```
macOS / Linux:
```
cd OperatingSystemSimulator
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Run
```
python main.py              # Windows-XP style desktop (default; remembers the last desktop you used)
python main.py --skin 98    # the teal Kernel / 98 desktop
```
PyCharm: right-click `main.py` → *Run 'main'*.
Open an app by double-clicking a desktop icon, from the Start menu, or from the *My OS Lab* window. Right-click the desktop to change the wallpaper.

## 4. Run the tests
```
python -m pytest -q                      # all 104 tests (algorithms, input parsing, headless GUI)
python -m pytest -q tests/test_cpu_scheduling.py      # one module
python -m pytest --durations=10 -q       # show the slowest tests
```
The GUI tests run headless (they set `QT_QPA_PLATFORM=offscreen` themselves); no window opens.

## 5. Edit the interface with Qt Designer
```
pyside6-designer ui\\cpu_scheduling.ui         # any file in ui\\
pyside6-uic ui\\cpu_scheduling.ui -o gui\\ui_cpu_scheduling.py      # optional: generate Python from a .ui file
```
The app loads the `.ui` files at run time (`QUiLoader`), so you only need *save in Designer → run `python main.py`*. Widgets are found by `objectName` (e.g. `btnRun`, `tblLedger`);
keep those names when editing. Colours come from `gui/theme.py` and `gui/xp_theme.py`; reference QSS copies are in `gui/styles/`.
`tools/make_ui.py` is the script that originally generated the `.ui` files — **do not run it after editing in Designer** (it overwrites them).

## 6. Optional tools
```
python tools/screenshots.py out_folder light      # render every Kernel / 98 page to PNG (offscreen)
python tools/bench.py                             # rough repaint / window-drag timings
python tools/extract_icons.py figma.pdf assets/icons   # needs pymupdf, pillow, numpy
```

## 7. Troubleshooting
| Symptom | Fix |
|---|---|
| `ModuleNotFoundError: No module named 'PySide6'` | the venv is not active / run `pip install -r requirements.txt` in the PyCharm terminal |
| `pyside6-designer` not found | activate the venv (it lives in `.venv\\Scripts`), or run `python -m PySide6.scripts.pyside_tool designer` |
| Window looks blurry on a scaled (125 %/150 %) display | normal Qt high-DPI scaling; set the Windows display scale to 100 % or use `set QT_SCALE_FACTOR_ROUNDING_POLICY=PassThrough` before running |
| *Compare policies* says Matplotlib is missing | `pip install matplotlib` |
| Preferences / wallpaper reset | they are stored with `QSettings` (Windows registry key *Kernel98 → OSSimulator*); delete it to start fresh |
| Tests fail with a Qt platform error on a headless server | `set QT_QPA_PLATFORM=offscreen` (Linux: `export QT_QPA_PLATFORM=offscreen`) |
