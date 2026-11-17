"""Banker's algorithm: need matrix, safety algorithm, resource-request algorithm."""
from typing import List, Sequence

from models.records import SafetyResult, SafetyStep, RequestResult
from utils.validators import ValidationError, check_matrix


def need_matrix(allocation, maximum):
    return [[mx - al for mx, al in zip(mr, ar)] for mr, ar in zip(maximum, allocation)]


def validate_state(available: Sequence[int], allocation, maximum):
    n, m = len(allocation), len(available)
    if n == 0:
        raise ValidationError("Add at least one process.")
    if m == 0:
        raise ValidationError("Define at least one resource type.")
    check_matrix([list(available)], 1, m, "Available")
    check_matrix(allocation, n, m, "Allocation")
    check_matrix(maximum, n, m, "Maximum")
    for i in range(n):
        for j in range(m):
            if allocation[i][j] > maximum[i][j]:
                raise ValidationError(
                    f"P{i}: allocation ({allocation[i][j]}) exceeds maximum demand ({maximum[i][j]}) "
                    f"for resource {j}. The matrices are inconsistent.")


def is_safe(available, allocation, maximum, names=None) -> SafetyResult:
    validate_state(available, allocation, maximum)
    n, m = len(allocation), len(available)
    need = need_matrix(allocation, maximum)
    work = list(available)
    finished = [False] * n
    seq, steps = [], []
    progress = True
    while progress:                       # repeated passes, scanning P0..Pn-1 in order
        progress = False
        for i in range(n):
            if finished[i] or any(need[i][j] > work[j] for j in range(m)):
                continue
            before = tuple(work)
            work = [work[j] + allocation[i][j] for j in range(m)]
            finished[i] = True
            seq.append(i)
            steps.append(SafetyStep(f"P{i}", before, tuple(work)))
            progress = True
    return SafetyResult(len(seq) == n, seq, steps, [i for i in range(n) if not finished[i]], need)


def request_resources(pid: int, request: Sequence[int], available, allocation, maximum) -> RequestResult:
    validate_state(available, allocation, maximum)
    n, m = len(allocation), len(available)
    if not 0 <= pid < n:
        raise ValidationError(f"Process index {pid} does not exist (0..{n - 1}).")
    if len(request) != m:
        raise ValidationError(f"Request needs {m} values, got {len(request)}.")
    if any((not isinstance(v, int)) or v < 0 for v in request):
        raise ValidationError("Request values must be non-negative integers.")
    need = need_matrix(allocation, maximum)
    if any(request[j] > need[pid][j] for j in range(m)):
        return RequestResult(False, f"P{pid} asked for more than its declared maximum claim.", None)
    if any(request[j] > available[j] for j in range(m)):
        return RequestResult(False, f"Resources not available: P{pid} must wait.", None)
    new_av = [available[j] - request[j] for j in range(m)]
    new_al = [list(r) for r in allocation]
    for j in range(m):
        new_al[pid][j] += request[j]
    res = is_safe(new_av, new_al, maximum)
    if res.safe:
        return RequestResult(True, "Request can be granted: the resulting state is safe.", res)
    return RequestResult(False, "Request denied: granting it would leave the system in an UNSAFE state.", res)
