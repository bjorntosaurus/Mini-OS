"""Banker's algorithm: need matrix, safety algorithm, resource-request algorithm."""
from typing import List, Sequence

from models.records import SafetyResult, SafetyStep, RequestResult
from utils.validators import ValidationError, check_matrix


# Need[i][j] = Max[i][j] - Allocation[i][j]: what process i may still request of resource j.
def need_matrix(allocation, maximum):
    """Return the Need matrix (Maximum - Allocation), one row per process."""
    return [[mx - al for mx, al in zip(mr, ar)] for mr, ar in zip(maximum, allocation)]


def validate_state(available: Sequence[int], allocation, maximum):
    # n = number of processes, m = number of resource types.
    """Raise ValidationError unless Available/Allocation/Maximum describe a consistent system
    (>=1 process, >=1 resource, matching shapes, non-negative, Allocation <= Maximum).
    """
    n, m = len(allocation), len(available)
    if n == 0:
        raise ValidationError("Add at least one process.")
    if m == 0:
        raise ValidationError("Define at least one resource type.")
    # Shape / sign checks: Allocation and Maximum must be n x m, Available 1 x m, all non-negative integers.
    check_matrix([list(available)], 1, m, "Available")
    check_matrix(allocation, n, m, "Allocation")
    check_matrix(maximum, n, m, "Maximum")
    # A process can never hold more than its declared maximum, otherwise Need would be negative (inconsistent input).
    for i in range(n):
        for j in range(m):
            if allocation[i][j] > maximum[i][j]:
                raise ValidationError(
                    f"P{i}: allocation ({allocation[i][j]}) exceeds maximum demand ({maximum[i][j]}) "
                    f"for resource {j}. The matrices are inconsistent.")


def is_safe(available, allocation, maximum, names=None) -> SafetyResult:
    """Banker's safety algorithm.

    Returns SafetyResult(safe, sequence, steps, unfinished, need). `steps` records Work before/after each
    finished process so the GUI can show the Work trace; `sequence` holds process indexes.
    """
    validate_state(available, allocation, maximum)
    n, m = len(allocation), len(available)
    need = need_matrix(allocation, maximum)
    # Work starts as the free resources and grows each time a finished process returns what it holds.
    work = list(available)
    # finished[i] = process i was able to run to completion in the simulated schedule.
    finished = [False] * n
    seq, steps = [], []
    # Safety algorithm: sweep P0..Pn-1 repeatedly; stop when a whole sweep finds nobody who can finish.
    progress = True
    while progress:                       # repeated passes, scanning P0..Pn-1 in order
        progress = False
        for i in range(n):
            # Skip finished processes and those whose remaining Need does not fit in Work (they would have to wait).
            if finished[i] or any(need[i][j] > work[j] for j in range(m)):
                continue
            # Pretend process i runs to completion and releases everything it holds: Work += Allocation[i].
            before = tuple(work)
            work = [work[j] + allocation[i][j] for j in range(m)]
            finished[i] = True
            seq.append(i)
            steps.append(SafetyStep(f"P{i}", before, tuple(work)))
            progress = True
    # SAFE iff every process finished (seq is then a safe sequence); otherwise the unfinished ones may deadlock.
    return SafetyResult(len(seq) == n, seq, steps, [i for i in range(n) if not finished[i]], need)


def request_resources(pid: int, request: Sequence[int], available, allocation, maximum) -> RequestResult:
    """Banker's resource-request algorithm for process `pid` asking for the vector `request`.

    Returns RequestResult(granted, reason, safety). Never mutates the input matrices.
    """
    validate_state(available, allocation, maximum)
    n, m = len(allocation), len(available)
    # Input checks: valid process index, exactly one value per resource, non-negative integers.
    if not 0 <= pid < n:
        raise ValidationError(f"Process index {pid} does not exist (0..{n - 1}).")
    if len(request) != m:
        raise ValidationError(f"Request needs {m} values, got {len(request)}.")
    if any((not isinstance(v, int)) or v < 0 for v in request):
        raise ValidationError("Request values must be non-negative integers.")
    need = need_matrix(allocation, maximum)
    # Resource-request step 1: a process may not ask for more than its declared remaining need.
    if any(request[j] > need[pid][j] for j in range(m)):
        return RequestResult(False, f"P{pid} asked for more than its declared maximum claim.", None)
    # Step 2: if the resources are not free right now the process must wait (request is not granted yet).
    if any(request[j] > available[j] for j in range(m)):
        return RequestResult(False, f"Resources not available: P{pid} must wait.", None)
    # Step 3: build the HYPOTHETICAL state after granting (Available down, Allocation up).
    # The caller's matrices are never modified.
    new_av = [available[j] - request[j] for j in range(m)]
    new_al = [list(r) for r in allocation]
    for j in range(m):
        new_al[pid][j] += request[j]
    # Step 4: grant only if the hypothetical state is safe; otherwise the request is denied (rolled back).
    res = is_safe(new_av, new_al, maximum)
    if res.safe:
        return RequestResult(True, "Request can be granted: the resulting state is safe.", res)
    return RequestResult(False, "Request denied: granting it would leave the system in an UNSAFE state.", res)
