"""Page replacement: FIFO, LRU, Optimal.

A replaced page takes over the frame slot of its victim.  Optimal ties (several resident
pages never used again) are broken by the lowest frame slot."""
from bisect import bisect_right
from collections import deque
from typing import List

from models.records import ReplStep, ReplResult
from utils.validators import ValidationError

ALGORITHMS = ("FIFO", "LRU", "OPTIMAL")


def simulate(refs: List[int], num_frames: int, algorithm: str) -> ReplResult:
    algorithm = algorithm.upper()
    if algorithm not in ALGORITHMS:
        raise ValidationError(f"Unknown algorithm '{algorithm}'.")
    if not refs:
        raise ValidationError("The reference string is empty.")
    if num_frames < 1:
        raise ValidationError("At least 1 frame is required.")
    if any(r < 0 for r in refs):
        raise ValidationError("Page numbers cannot be negative.")

    frames = [None] * num_frames
    slot_of = {}
    fifo = deque()
    last_use = {}
    positions = {}
    if algorithm == "OPTIMAL":
        for i, r in enumerate(refs):
            positions.setdefault(r, []).append(i)

    steps, faults = [], 0
    for i, page in enumerate(refs):
        last_use[page] = i
        if page in slot_of:
            steps.append(ReplStep(i, page, list(frames), False, None, None))
            continue
        faults += 1
        evicted = None
        if None in frames:
            slot = frames.index(None)
        else:
            if algorithm == "FIFO":
                victim = fifo.popleft()
            elif algorithm == "LRU":
                victim = min((p for p in slot_of), key=lambda p: last_use[p])
            else:
                def next_use(p):
                    pos = positions[p]
                    k = bisect_right(pos, i)
                    return pos[k] if k < len(pos) else float("inf")
                victim = max(slot_of, key=lambda p: (next_use(p), -slot_of[p]))
            slot = slot_of.pop(victim)
            evicted = victim
        frames[slot] = page
        slot_of[page] = slot
        fifo.append(page)
        steps.append(ReplStep(i, page, list(frames), True, evicted, slot))

    n = len(refs)
    if algorithm == "FIFO":
        queue, labels = list(fifo), ("OLDEST", "NEWEST")
    elif algorithm == "LRU":
        queue, labels = sorted(slot_of, key=lambda p: last_use[p]), ("LEAST RECENT", "MOST RECENT")
    else:
        queue, labels = [p for p in frames if p is not None], ("FRAME 1", f"FRAME {num_frames}")
    return ReplResult(algorithm, steps, faults, n - faults, faults / n, (n - faults) / n, queue, labels)
