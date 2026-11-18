"""Contiguous memory allocation and fragmentation.

mode='fixed'   : every block is a fixed partition holding at most one process; the unused
                 part of an occupied block is INTERNAL fragmentation.
mode='dynamic' : a block is a hole; a process is carved out of it and the remainder stays a
                 hole (no internal fragmentation).
EXTERNAL fragmentation = total free memory when some process could not be placed even
though the free memory in total would have been large enough (i.e. it is scattered)."""
from typing import List

from models.records import BlockReport, FragResult
from utils.validators import ValidationError

STRATEGIES = ("first", "best", "worst", "next")
MODES = ("fixed", "dynamic")


def allocate(blocks: List[int], processes: List[int], strategy: str = "first", mode: str = "fixed") -> FragResult:
    # ---- validation ----
    """Place `processes` (sizes) into memory `blocks` (sizes) and measure fragmentation.

    Args:
        strategy: 'first', 'best', 'worst' or 'next' fit.
        mode: 'fixed' (one process per partition) or 'dynamic' (blocks are holes that get split).
    Returns:
        FragResult with a per-block report, the process->block assignment, unallocated processes,
        used / internal / external / free totals and the largest free hole.
    """
    if strategy not in STRATEGIES:
        raise ValidationError(f"Unknown strategy '{strategy}'.")
    if mode not in MODES:
        raise ValidationError(f"Unknown mode '{mode}'.")
    if not blocks:
        raise ValidationError("Define at least one memory block.")
    if not processes:
        raise ValidationError("Define at least one process.")
    if any(b < 1 for b in blocks):
        raise ValidationError("Block sizes must be at least 1.")
    if any(p < 1 for p in processes):
        raise ValidationError("Process sizes must be at least 1.")

    # remaining[b] = free bytes left in block b; occupied[b] = fixed-mode flag (one process per block);
    # placed[b] = processes put in block b; assign[p] = block chosen for process p (None = could not be placed).
    nb = len(blocks)
    remaining = list(blocks)
    occupied = [False] * nb
    placed = [[] for _ in range(nb)]
    assign = [None] * len(processes)
    # Next-fit remembers where the previous allocation happened and continues searching from there.
    pointer = 0
    # Allocate processes in the order given (arrival order).
    for pi, size in enumerate(processes):
        # A block can host the process if it is free and big enough (fixed), or simply has enough room left (dynamic).
        def fits(b):
            return (not occupied[b] and remaining[b] >= size) if mode == "fixed" else remaining[b] >= size
        # All blocks that could host this process; the strategy picks one of them.
        cands = [b for b in range(nb) if fits(b)]
        if not cands:
            continue
        # first fit = lowest-numbered candidate;  best fit = smallest candidate (least leftover);
        # worst fit = largest candidate;  next fit = first candidate at/after the pointer, wrapping around.
        if strategy == "first":
            b = cands[0]
        elif strategy == "best":
            b = min(cands, key=lambda x: (remaining[x], x))
        elif strategy == "worst":
            b = max(cands, key=lambda x: (remaining[x], -x))
        else:
            b = next(x for x in [(pointer + k) % nb for k in range(nb)] if x in cands)
            pointer = b
        # Commit the allocation. In dynamic mode the hole shrinks and the remainder stays available as a smaller hole.
        assign[pi] = b
        placed[b].append(pi)
        occupied[b] = True
        if mode == "dynamic":
            remaining[b] -= size

    # Per-block accounting.
    # Fixed mode: INTERNAL fragmentation = block size - process size inside an occupied block; an untouched block is free.
    # Dynamic mode: no internal fragmentation, the leftover is a free hole.
    reports, internal, free_total, largest = [], 0, 0, 0
    for b in range(nb):
        used = sum(processes[p] for p in placed[b])
        if mode == "fixed":
            inter = blocks[b] - used if placed[b] else 0
            free = 0 if placed[b] else blocks[b]
        else:
            inter, free = 0, blocks[b] - used
        internal += inter
        free_total += free
        largest = max(largest, free)
        reports.append(BlockReport(b, blocks[b], placed[b], used, inter, free))
    # External fragmentation: free memory exists in total (>= some waiting process) but is split into holes that are each too
    # small.  If a process is bigger than ALL free memory combined it is simply 'out of memory', not fragmentation.
    unalloc = [i for i, a in enumerate(assign) if a is None]
    external = free_total if any(processes[i] <= free_total for i in unalloc) else 0
    return FragResult(strategy, mode, reports, assign, unalloc, sum(blocks),
                      sum(r.used for r in reports), internal, free_total, external, largest)
