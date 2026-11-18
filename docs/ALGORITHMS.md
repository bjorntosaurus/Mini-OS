# Algorithm reference
Source: `algorithms/*.py` (pure Python, no GUI code). Every function has a docstring and every logical block a comment.
Each simulator validates input first and raises `ValidationError` with a readable message; the GUI shows it in a dialog.

| Module | Entry point | Notes |
|---|---|---|
| `cpu_scheduling.py` | `schedule(processes, algorithm, quantum, preemptive)` | FCFS, SJF/SRTF, Priority, Round Robin |
| `bankers_algorithm.py` | `is_safe(...)`, `request_resources(...)`, `need_matrix(...)` | safety + resource-request algorithms |
| `paging.py` | `translate(logical, page_size, table, num_frames)` | page table lookup |
| `page_replacement.py` | `simulate(refs, num_frames, algorithm)` | FIFO, LRU, Optimal |
| `segmentation.py` | `translate(segments, seg_id, offset)` | base + limit protection |
| `fragmentation.py` | `allocate(blocks, processes, strategy, mode)` | first/best/worst/next fit |
| `disk_scheduling.py` | `schedule(algorithm, head, requests, lo, hi, direction, count_return)` | FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK |
| `multiprogramming.py` | `cpu_utilization(n, p)`, `simulate(programs, ...)` | U = 1 − pⁿ + tick simulation |

## CPU scheduling
Each step picks one process from those that have arrived: FCFS = earliest arrival; SJF = shortest burst (SRTF: shortest *remaining* time, re-checked at every arrival);
Priority = lowest number (preemptive: re-checked at every arrival); Round Robin = FIFO queue, `quantum` units per turn (arrivals during a turn queue before the pre-empted process).
Ties → earlier arrival → input order. Idle gaps appear as idle blocks. Turnaround = completion − arrival, waiting = turnaround − burst, response = first start − arrival.

## Banker's algorithm
Need = Max − Allocation. Safety: `Work = Available`; repeatedly find an unfinished process with `Need ≤ Work`, add its Allocation to Work, mark it finished.
All finished ⇒ safe (the order found is a safe sequence). Request(Pi): must be ≤ Need[i], then ≤ Available, then pretend to grant and re-run the safety check; grant only if still safe.

## Paging
`page = address ÷ page size`, `offset = address mod page size`. Page outside the table ⇒ invalid address; valid flag No ⇒ page fault; otherwise `physical = frame × page size + offset`.

## Page replacement
Frame slots hold pages; a new page on a fault takes the slot of its victim. FIFO evicts the longest-resident page, LRU the least recently used, Optimal the page whose next use is farthest away (ties → lowest slot).
Hit ratio = hits ÷ references, fault ratio = faults ÷ references.

## Segmentation
Legal iff the segment exists and `0 ≤ offset < limit`; then `physical = base + offset`. Otherwise a trap is reported. Segments may not overlap physically.

## Fragmentation
Fixed mode: one process per block, wasted space inside an occupied block is **internal** fragmentation. Dynamic mode: blocks are holes that are split.
**External** fragmentation = total free memory when some waiting process would fit in the total but not in any single hole. Strategies: first (lowest block), best (smallest fit), worst (largest), next (continue from the last allocation).

## Disk scheduling
FCFS in arrival order; SSTF nearest request next; SCAN sweeps to the disk edge then reverses; LOOK reverses at the last request; C-SCAN sweeps to the edge then jumps to the other end (no service) and sweeps again;
C-LOOK jumps to the lowest pending request. Direction "down" is computed by mirroring the cylinders. Total = sum of |Δcylinder| (return jumps optional).

## Multiprogramming
Model: U = 1 − pⁿ. Simulation per tick: admit programs that fit in memory (and resource units) → each resident program is I/O-blocked with its own probability (seeded) → one ready program runs (round robin) → finished programs free their memory.
