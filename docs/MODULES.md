# Module documentation
The simulator has **eight modules**. Each one has: a window in the GUI (`gui/pages/*_page.py` + a Qt Designer file in `ui/`), a pure-Python algorithm module
(`algorithms/*.py`, no Qt), shared data records (`models/records.py`), input validation (`utils/validators.py`, `utils/parsers.py`) and an automated test suite (`tests/`).
Short algorithm-only summary: [ALGORITHMS.md](ALGORITHMS.md). All apps open **empty**; nothing is pre-loaded.

| # | Window (XP name) | Module | Algorithm file | GUI file | Tests |
|---|---|---|---|---|---|
| 1 | Dispatch | CPU scheduling | `cpu_scheduling.py` | `cpu_page.py` | `test_cpu_scheduling.py` |
| 2 | Safehouse | Banker's algorithm | `bankers_algorithm.py` | `bankers_page.py` | `test_bankers.py` |
| 3 | Pageport | Paging | `paging.py` | `paging_page.py` | `test_paging.py` |
| 4 | Framelog | Page replacement | `page_replacement.py` | `pagerep_page.py` | `test_page_replacement.py` |
| 5 | Segment Studio | Segmentation | `segmentation.py` | `segmentation_page.py` | `test_segmentation.py` |
| 6 | Gapscan | Fragmentation | `fragmentation.py` | `fragmentation_page.py` | `test_fragmentation.py` |
| 7 | Seek | Disk scheduling | `disk_scheduling.py` | `disk_page.py` | `test_disk_scheduling.py` |
| 8 | Resident | Multiprogramming | `multiprogramming.py` | `multi_page.py` | `test_multiprogramming.py` |

**General input rules.** No fixed limits on the number of processes, resources, frames, pages, segments, blocks, requests or programs. Empty, non-numeric, negative or inconsistent input never crashes the app:
a message names the problem (and the line number for pasted text). Where one-row-at-a-time entry would be slow there is an **Edit as text / Paste list** box that accepts a whole table
(spaces, commas, tabs or an Excel paste; `#` starts a comment; a header line is skipped). Parsers: `utils/parsers.py`.

---
## 1. CPU scheduling — *Dispatch*
**Purpose.** Decide which ready process gets the CPU and measure how good the schedule is.
**Algorithms.** FCFS · SJF (non-preemptive) and SRTF (preemptive SJF) · Priority (non-preemptive / preemptive, lower number = higher priority) · Round Robin (time quantum).
**Input.** Process rack: `id`, `arrival`, `burst` (+ `priority` for Priority). Press **Enter** in a row for the next row (last row → new row). **Edit as text…**: one `id arrival burst [priority]` per line (without id → P1, P2…). Quantum box for Round Robin, *Preemptive* checkbox for SJF/Priority.
**Output.** Gantt chart with First / Play / Step playback · timing ledger (start, finish = completion, wait, turnaround) · average waiting & turnaround time · CPU busy % · throughput · execution order (status bar / *Timeline → Show execution order*) · *Compare policies* bar chart (Matplotlib) · CSV export.
**Method.** Event-driven simulation: pick the process with the best sort key among those that have arrived (FCFS = arrival, SJF = burst/remaining, Priority = priority; ties → arrival → input order); run it to completion, or (preemptive) until the next arrival. Round Robin keeps a FIFO queue and gives each process ≤ quantum units; arrivals during a slice queue before the pre-empted process.
**Formulas.** turnaround = completion − arrival · waiting = turnaround − burst · response = first start − arrival · CPU busy = busy time ÷ (last completion − first arrival) · throughput = processes ÷ same span.
**Validation.** ≥ 1 process; unique non-empty IDs; arrival ≥ 0; burst ≥ 1; quantum ≥ 1; numeric fields.
**Complexity.** Priority-based engines O(n · slices) ≈ O(n²) worst case; RR O(Σburst ÷ quantum).

## 2. Banker's algorithm — *Safehouse*
**Purpose.** Decide whether a resource-allocation state is *safe* (no deadlock possible) and whether a new request can be granted.
**Input.** Per resource type an *Available* count (cards on top); the **Resource audit** table with *Allocated* and *Maximum* cells (one number per resource, space separated). **+ Process / − Process / + Resource / − Resource** change the size.
**Enter matrices…** takes Available (one line) + Allocation and Maximum (one line per process) in one box. **Request sandbox**: choose a process, enter a request vector, *Check this request*, optionally *Apply granted request*.
**Output.** Need matrix (Maximum − Allocated) · SAFE / UNSAFE badge with "k / n can finish" · safe sequence boxes · Work trace `(3,3,2) → (5,3,2) → …` · reason when a request is denied.
**Method.** *Safety:* Work = Available; repeatedly sweep P0…Pn-1 and finish any unfinished process with Need ≤ Work (Work += its Allocation). All finished ⇒ safe. *Request(Pi):* (1) request ≤ Need[i], else error; (2) request ≤ Available, else wait; (3) pretend to grant; (4) grant only if the new state is safe.
**Validation.** n ≥ 1, m ≥ 1, equal row widths, non-negative integers, Allocation ≤ Maximum, valid process index.
**Complexity.** O(m · n²).

## 3. Paging — *Pageport*
**Purpose.** Translate logical addresses to physical addresses through a page table.
**Input.** Logical address; page size (list or any number); number of physical frames; page directory rows (*Frame*, *Valid* Yes/No) with **+ Page / − Page**, or **Edit as text…** (`3 1 5 2 -` = frame of each page, `-` = not resident; `page:frame` pairs also work).
**Output.** Split (page, offset) → lookup (frame, valid) → physical address; the formula; physical RAM frame map highlighting the used frame; messages for page fault / invalid address.
**Method.** `page = address ÷ page size`, `offset = address mod page size`. Page ≥ table length ⇒ **invalid address**; entry not valid ⇒ **page fault**; otherwise `physical = frame × page size + offset`.
**Validation.** Page size ≥ 1, frames ≥ 1, address ≥ 0 and numeric, frame numbers exist (< frames) and are unique among valid pages.
**Complexity.** O(1) per translation (validation O(pages)).

## 4. Page replacement — *Framelog*
**Purpose.** Compare FIFO, LRU and Optimal when memory is smaller than the pages used.
**Input.** Reference string (any length: `7, 0, 1, 2, 0, 3, 0, 4` — commas or spaces) and a frame count (− / +). Choose FIFO / LRU / Optimal; **Replay** animates it.
**Output.** Frame-by-frame history (green = hit, highlighted = selected fault; click a column to inspect the step) · event inspector (page, hit/fault, evicted page and frame) · total faults, hits, hit ratio, fault ratio · final residence queue.
**Method.** A new page takes a free frame, otherwise the victim's frame slot. FIFO victim = longest resident; LRU = least recently used; Optimal = the page whose next use is farthest in the future (never again = ∞, ties → lowest slot).
**Validation.** Non-empty list of non-negative integers; frames ≥ 1.
**Complexity.** FIFO O(n); LRU O(n·f); Optimal O(n·f·log n) (f = frames).

## 5. Segmentation — *Segment Studio*
**Purpose.** Show base-and-limit address translation and protection.
**Input.** Segments (id, name, base, limit, protection) via **+ Add segment** (double-click a card to edit, × to delete) or **Edit as text…** (`id [name] base limit [r|rw|rx|rwx]`). Probe: segment number + offset.
**Output.** Segment table cards · physical memory map with gaps · bounds inspector: base, limit, offset, verdict `offset < limit`, physical address or **trap** with the reason.
**Method.** Legal iff the segment exists and `0 ≤ offset < limit`; then `physical = base + offset`.
**Validation.** Unique non-negative IDs; base ≥ 0; limit ≥ 1; **no physical overlap** (touching is fine); numeric offset.
**Complexity.** O(s log s) (table validation).

## 6. Fragmentation — *Gapscan*
**Purpose.** Show how allocation strategies waste memory.
**Input.** **Setup ✎**: memory block sizes, process sizes (comma/space/line lists of any length), strategy (first / best / worst / next fit) and model (fixed or dynamic partitions). Internal / External view toggle; export a text report.
**Output.** Per-partition used/wasted bars · audit panel (internal waste KB and % of allocated memory, total, used, external) · efficiency bar · unallocated processes · explanation ("why not compact?").
**Method.** Allocate processes in order. First = lowest fitting block, best = smallest fitting, worst = largest, next = continue after the last allocation. *Fixed:* one process per block; unused part of an occupied block = **internal fragmentation**. *Dynamic:* blocks are holes that are split. **External fragmentation** = free memory in total when a waiting process would fit in the total but in no single hole.
**Validation.** ≥ 1 block and ≥ 1 process; sizes ≥ 1.
**Complexity.** O(processes × blocks).

## 7. Disk scheduling — *Seek*
**Purpose.** Compare head-movement of the classic disk algorithms.
**Input.** **+ Edit request queue**: head position, min / max cylinder, direction (up/down), request list (any length), and whether C-SCAN / C-LOOK return jumps count. Pick FCFS · SSTF · SCAN · C-SCAN · LOOK · C-LOOK, then **Trace disk head**.
**Output.** Head-movement plot (cylinder × request order) · request ledger (order, cylinder, seek distance) · total cylinders moved · average seek · requests serviced.
**Method.** FCFS: arrival order. SSTF: nearest request next. SCAN: sweep to the disk **edge**, reverse. LOOK: reverse at the **last request**. C-SCAN: sweep to the edge, **jump** to the other end without serving, sweep again. C-LOOK: jump to the lowest pending request. "Down" runs the same logic on mirrored cylinders. Total = Σ|Δcylinder|.
**Validation.** min < max; head and every request inside the range; non-empty queue; integer cylinders.
**Complexity.** FCFS O(n); SSTF O(n²); SCAN/LOOK families O(n log n).

## 8. Multiprogramming — *Resident*
**Purpose.** Show why several programs in memory keep the CPU busy, and simulate real sharing of memory and resources.
**Input.** Programs (name, memory MB, CPU ticks, I/O-wait %, resource units, arrival) via **+ Add program** (click a card to edit/delete) or **Paste list…** (`name memory cpu io% [resources] [arrival]`). Click the memory badge for system memory, resource units, quantum and seed. What-if console: degree *n* and I/O-wait probability *p*.
**Output.** *Model view:* U = 1 − pⁿ and the utilisation curve (click to pick n). *Simulation view:* per-program state timeline (running / ready / I/O wait / queued / done), tick slider that updates the cards and the memory badge, measured CPU utilisation vs. the model, average memory use, peak memory, maximum degree, average turnaround.
**Method.** Each tick: (1) admit arrived programs that fit in memory and resource units, others stay queued; (2) each resident program is blocked on I/O with its own probability (seeded RNG → reproducible); (3) one ready program runs (round robin, `quantum` ticks); (4) a program with all CPU time received finishes and frees its memory/resources.
**Validation.** Memory ≥ 1 and ≤ total memory; CPU time ≥ 1; I/O wait 0–99 %; unique names; arrival ≥ 0; resource units ≤ total.
**Complexity.** O(ticks × programs).

---
## Shared infrastructure
| Part | Files | Role |
|---|---|---|
| Desktops | `gui/xp_desktop.py`, `gui/main_window.py` | Windows-XP desktop (default) and Kernel / 98 desktop; windows, taskbar, Start menu, shortcuts |
| Pages | `gui/pages/` | one class per module; they only collect input, call the algorithm and show results |
| Custom drawing | `gui/widgets/charts.py` | Gantt, frame history, disk plot, memory map, curves, timelines |
| Themes | `gui/theme.py`, `gui/xp_theme.py`, `gui/wallpapers.py` | palettes (light/dark), QSS, wallpapers (built-in + your pictures) |
| Records & validation | `models/records.py`, `utils/validators.py`, `utils/parsers.py` | dataclasses, number parsing, bulk text parsing |
| Interface files | `ui/*.ui` | Qt Designer layouts loaded at run time |
