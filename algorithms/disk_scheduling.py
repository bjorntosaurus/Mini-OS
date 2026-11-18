"""Disk scheduling: FCFS, SSTF, SCAN, C-SCAN, LOOK, C-LOOK.

SCAN / C-SCAN always sweep to the physical end of the disk (min/max cylinder) while
LOOK / C-LOOK only travel as far as the last request.  C-SCAN / C-LOOK jump back to the
opposite side without servicing; the jump is counted in head movement unless
count_return=False."""
from typing import List

from models.records import DiskResult
from utils.validators import ValidationError

ALGORITHMS = ("FCFS", "SSTF", "SCAN", "CSCAN", "LOOK", "CLOOK")


# Build the head path for an UPWARD start (the 'down' direction is handled by mirroring, see schedule()).
# upper = requests at/above the head (served on the first sweep); lower = requests below it (served after the turn).
def _up_steps(algo, head, reqs, lo, hi):
    """Steps (position, kind) for an upward start. kind: S service, B waypoint, J jump, JS jump that lands on a request."""
    upper = sorted(r for r in reqs if r >= head)
    lower = sorted(r for r in reqs if r < head)
    # The path always starts at the head's current position.
    steps = [(head, "B")]
    steps += [(r, "S") for r in upper]
    # SCAN (elevator): sweep to the physical END of the disk, reverse, then serve the rest while moving back down.
    if algo == "SCAN":
        if steps[-1][0] != hi:
            steps.append((hi, "B"))
        steps += [(r, "S") for r in reversed(lower)]
    # LOOK: like SCAN but turns around at the last request instead of travelling to the disk edge.
    elif algo == "LOOK":
        steps += [(r, "S") for r in reversed(lower)]
    # C-SCAN: sweep to the end, then JUMP to the start (no service during the jump) and sweep upward again.
    elif algo == "CSCAN":
        if steps[-1][0] != hi:
            steps.append((hi, "B"))
        if lower:
            steps.append((lo, "J"))
            steps += [(r, "S") for r in lower]
    # C-LOOK: like C-SCAN but jumps back only to the lowest pending request, not to cylinder 0.
    elif algo == "CLOOK":
        if lower:
            steps.append((lower[0], "JS"))          # jump straight to the lowest request
            steps += [(r, "S") for r in lower[1:]]
    return steps


# Public entry point.
def schedule(algorithm: str, head: int, requests: List[int], lo: int = 0, hi: int = 199,
             direction: str = "up", count_return: bool = True) -> DiskResult:
    # ---- validation: algorithm name, range, head and every request inside [lo, hi], direction ----
    """Compute the head path for FCFS / SSTF / SCAN / C-SCAN / LOOK / C-LOOK.

    Args:
        head: starting cylinder; requests: cylinders to serve (any length, duplicates allowed).
        lo, hi: first and last cylinder of the disk. direction: 'up' or 'down' (ignored by FCFS/SSTF).
        count_return: whether the C-SCAN / C-LOOK return jump counts towards total head movement.
    Returns:
        DiskResult(path, order, seeks, total, average, kinds).
    """
    algo = algorithm.upper().replace("-", "")
    if algo not in ALGORITHMS:
        raise ValidationError(f"Unknown algorithm '{algorithm}'.")
    if lo >= hi:
        raise ValidationError("Minimum cylinder must be smaller than the maximum cylinder.")
    if not lo <= head <= hi:
        raise ValidationError(f"Head position {head} is outside the disk range {lo}-{hi}.")
    if not requests:
        raise ValidationError("The request queue is empty.")
    bad = [r for r in requests if not lo <= r <= hi]
    if bad:
        raise ValidationError(f"Request(s) {bad[:5]} are outside the disk range {lo}-{hi}.")
    if direction not in ("up", "down"):
        raise ValidationError("Direction must be 'up' or 'down'.")

    # FCFS: serve in arrival order.
    if algo == "FCFS":
        steps = [(head, "B")] + [(r, "S") for r in requests]
    # SSTF: always serve the pending request closest to the head (ties: earliest in the queue).
    elif algo == "SSTF":
        pending, pos, steps = list(requests), head, [(head, "B")]
        while pending:
            r = min(pending, key=lambda x: abs(x - pos))      # ties: earliest in queue
            pending.remove(r)
            steps.append((r, "S"))
            pos = r
    else:
        # Direction 'down' = reflect every cylinder (x -> lo+hi-x), run the upward algorithm, reflect the path back.
        # This guarantees up/down behave symmetrically.
        mirror = direction == "down"
        f = (lambda x: lo + hi - x) if mirror else (lambda x: x)
        steps = _up_steps(algo, f(head), [f(r) for r in requests], lo, hi)
        steps = [(f(p), k) for p, k in steps]

    # Turn the step list into numbers:
    #   total = sum of |distance| between consecutive positions (jumps count only if count_return=True);
    #   seeks[k] = head movement attributed to the k-th SERVED request (includes any detour to the disk edge before it).
    path = [p for p, _ in steps]
    order, seeks, acc, total = [], [], 0, 0
    for idx in range(1, len(steps)):
        pos, kind = steps[idx]
        d = abs(pos - steps[idx - 1][0])
        if kind in ("J", "JS") and not count_return:
            d = 0
        total += d
        acc += d
        if kind in ("S", "JS"):
            order.append(pos)
            seeks.append(acc)
            acc = 0
    if acc and seeks:
        seeks[-1] += acc
    return DiskResult(algo, path, order, seeks, total, total / len(requests), [k for _, k in steps])
