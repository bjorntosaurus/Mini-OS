# Reference cases (used by the automated tests)
The apps open empty; type any of these in by hand to check a simulator. Nothing here is loaded automatically.
Every sample loads automatically (Settings → "Load example data") or via each page's **File → Load sample**.
All numbers below are asserted in `tests/`.

## 1. CPU scheduling — P1(0,5) P2(1,3) P3(2,1) P4(3,2)  (arrival, burst)
| Algorithm | Order | Avg wait | Avg turnaround |
|---|---|---|---|
| FCFS | P1 P2 P3 P4 | 4.00 | 6.75 (CPU 100 %, throughput 0.36/ms) |
| SJF (non-preemptive) | P1 P3 P4 P2 | 3.25 | 6.00 |
Textbook: P1(0,8) P2(1,4) P3(2,9) P4(3,5), SRTF → avg wait 6.5. RR q=4 on bursts 24,3,3 (all at 0) → waits 6,4,7.

## 2. Banker's algorithm
Available (3,3,2); Allocation P0..P4 = 010 200 302 211 002; Maximum = 753 322 902 222 433.
Need = 743 122 600 011 431 → SAFE, sequence **P1 → P3 → P4 → P0 → P2**, Work (3,3,2)→(5,3,2)→(7,4,3)→(7,4,5)→(7,5,5)→(10,5,7).
Request P1 = (1,0,2) → granted. After applying it, P0 requesting (0,2,0) is denied (unsafe).

## 3. Paging — page size 1024, 6 frames, table 0→3, 1→1, 2→5, 3→2, 4 invalid
Address 2172 → page 2, offset 124, frame 5, physical **5244**. Address 4100 → page fault. Address 999999 → invalid (outside address space).

## 4. Page replacement — 7,0,1,2,0,3,0,4 with 3 frames
FIFO: 7 faults, 1 hit, hit ratio 12.5 %, final queue 3→0→4.
Classic 20-page string 7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1, 3 frames: FIFO 15, LRU 12, Optimal 9 faults.

## 5. Segmentation — Code(1000,600) Data(2400,400) Stack(4000,800) Heap(5600,1200)
(segment 0, offset 240) → 1240. (segment 0, offset 600) → trap (offset ≥ limit). Unknown segment → trap.

## 6. Fragmentation
Blocks 256×4, processes 212 180 96 64 (fixed, first fit): internal waste **472 KB** (44+76+160+192), used 552, 46.1 % of allocated memory.
Blocks 100 500 200 300 600, processes 212 417 112 426 → first fit [500,600,200,—], best fit [300,500,200,600], worst fit [600,500,300,—].

## 7. Disk scheduling — head 53, range 0–199, queue 98 183 37 122 14 124 65 67 (direction up)
FCFS 640 · SSTF 236 · SCAN 331 · C-SCAN 382 (jump counted) · LOOK 299 · C-LOOK 322. SCAN with direction down = 236.

## 8. Multiprogramming
U = 1 − pⁿ: n=4, p=0.8 → **59.04 %**. Simulation: 4 programs × 128 MB, 25 CPU ticks, 80 % I/O wait, 1024 MB, seed 1 → measured CPU utilisation is close to the model (reproducible for a given seed).
