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
    # ---- validation ----
    """Simulate FIFO, LRU or OPTIMAL page replacement.

    Args:
        refs: page reference string (non-negative ints, any length).
        num_frames: number of physical frames (>= 1).
        algorithm: 'FIFO', 'LRU' or 'OPTIMAL'.
    Returns:
        ReplResult with one ReplStep per reference (frame snapshot, fault flag, evicted page, slot written),
        totals, hit/fault ratios and the final residence queue.
    """
    algorithm = algorithm.upper()
    if algorithm not in ALGORITHMS:
        raise ValidationError(f"Unknown algorithm '{algorithm}'.")
    if not refs:
        raise ValidationError("The reference string is empty.")
    if num_frames < 1:
        raise ValidationError("At least 1 frame is required.")
    if any(r < 0 for r in refs):
        raise ValidationError("Page numbers cannot be negative.")

    # frames[k] = page stored in frame slot k (None = empty). slot_of is the reverse map page -> slot (also 'is it resident?').
    frames = [None] * num_frames
    slot_of = {}
    # fifo: pages in the order they were loaded (front = oldest)  -> FIFO victim.
    # last_use: page -> index of its most recent reference -> LRU victim.
    fifo = deque()
    last_use = {}
    # Optimal needs the future: positions[page] = sorted list of every index where the page is referenced.
    positions = {}
    if algorithm == "OPTIMAL":
        for i, r in enumerate(refs):
            positions.setdefault(r, []).append(i)

    # Walk through the reference string one reference at a time, recording the frame contents after each.
    steps, faults = [], 0
    for i, page in enumerate(refs):
        # Every reference (hit or fault) refreshes the page's recency.
        last_use[page] = i
        # HIT: page already in a frame. Nothing is replaced (FIFO order is NOT refreshed by hits; LRU recency was just updated).
        if page in slot_of:
            steps.append(ReplStep(i, page, list(frames), False, None, None))
            continue
        # PAGE FAULT: the page must be brought in.
        faults += 1
        evicted = None
        # A free frame exists: use the first empty slot, nothing is evicted.
        if None in frames:
            slot = frames.index(None)
        else:
            if algorithm == "FIFO":
                # FIFO victim: the page that has been resident longest.
                victim = fifo.popleft()
            elif algorithm == "LRU":
                # LRU victim: the resident page whose last use is the oldest.
                victim = min((p for p in slot_of), key=lambda p: last_use[p])
            else:
                # Optimal victim: the resident page whose NEXT use is farthest in the future (never used again = infinity).
                # bisect finds the first future position in O(log n). Ties (several never used again) -> lowest frame slot.
                def next_use(p):
                    pos = positions[p]
                    k = bisect_right(pos, i)
                    return pos[k] if k < len(pos) else float("inf")
                victim = max(slot_of, key=lambda p: (next_use(p), -slot_of[p]))
            # The new page takes over the victim's frame slot (this is what the frame-history table displays).
            slot = slot_of.pop(victim)
            evicted = victim
        frames[slot] = page
        slot_of[page] = slot
        fifo.append(page)
        steps.append(ReplStep(i, page, list(frames), True, evicted, slot))

    # ---- summary ----
    # final_queue = the 'residence queue' shown to the user, ordered according to the policy.
    n = len(refs)
    if algorithm == "FIFO":
        queue, labels = list(fifo), ("OLDEST", "NEWEST")
    elif algorithm == "LRU":
        queue, labels = sorted(slot_of, key=lambda p: last_use[p]), ("LEAST RECENT", "MOST RECENT")
    else:
        queue, labels = [p for p in frames if p is not None], ("FRAME 1", f"FRAME {num_frames}")
    return ReplResult(algorithm, steps, faults, n - faults, faults / n, (n - faults) / n, queue, labels)
