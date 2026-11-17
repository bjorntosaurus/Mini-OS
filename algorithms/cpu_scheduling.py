"""CPU scheduling: FCFS, SJF / SRTF, Priority (non-preemptive or preemptive), Round Robin.

Conventions (documented in README):
* Lower priority number = higher priority.
* Ties are broken by earlier arrival, then by input order.
* Round Robin: processes that arrive while another is running are queued *before* the
  pre-empted process is re-queued.
* CPU busy % and throughput use the span  last completion - earliest arrival.
"""
from collections import deque
from typing import List, Optional

from models.records import Process, Slice, ProcMetrics, ScheduleResult
from utils.validators import ValidationError

ALGORITHMS = ("FCFS", "SJF", "PRIORITY", "RR")


def validate(processes: List[Process], algorithm: str, quantum: Optional[int]):
    if algorithm not in ALGORITHMS:
        raise ValidationError(f"Unknown algorithm '{algorithm}'.")
    if not processes:
        raise ValidationError("Add at least one process before running the queue.")
    seen = set()
    for p in processes:
        if not str(p.pid).strip():
            raise ValidationError("Every process needs an ID.")
        if p.pid in seen:
            raise ValidationError(f"Duplicate process ID '{p.pid}'.")
        seen.add(p.pid)
        if p.arrival < 0:
            raise ValidationError(f"{p.pid}: arrival time cannot be negative.")
        if p.burst < 1:
            raise ValidationError(f"{p.pid}: burst time must be at least 1.")
    if algorithm == "RR" and (quantum is None or quantum < 1):
        raise ValidationError("Round Robin needs a time quantum of at least 1.")


def _merge(slices):
    out = []
    for s in slices:
        if s.end <= s.start:
            continue
        if out and out[-1].pid == s.pid and out[-1].end == s.start:
            out[-1].end = s.end
        else:
            out.append(Slice(s.pid, s.start, s.end))
    return out


def _priority_engine(procs, algorithm, preemptive):
    n = len(procs)
    rem = [p.burst for p in procs]
    done = [False] * n
    finish = [0] * n
    slices = []
    t = min(p.arrival for p in procs)
    left = n

    def key(i):
        p = procs[i]
        if algorithm == "FCFS":
            return (p.arrival, i)
        if algorithm == "SJF":
            return ((rem[i] if preemptive else p.burst), p.arrival, i)
        return (p.priority, p.arrival, i)

    while left:
        ready = [i for i in range(n) if not done[i] and procs[i].arrival <= t]
        if not ready:
            nxt = min(procs[i].arrival for i in range(n) if not done[i])
            slices.append(Slice(None, t, nxt))
            t = nxt
            continue
        i = min(ready, key=key)
        run = rem[i]
        if preemptive and algorithm != "FCFS":
            arrivals = [procs[j].arrival for j in range(n) if not done[j] and procs[j].arrival > t]
            if arrivals:
                run = min(run, min(arrivals) - t)
        slices.append(Slice(procs[i].pid, t, t + run))
        t += run
        rem[i] -= run
        if rem[i] == 0:
            done[i] = True
            finish[i] = t
            left -= 1
    return slices, finish


def _rr_engine(procs, quantum):
    n = len(procs)
    rem = [p.burst for p in procs]
    finish = [0] * n
    order = sorted(range(n), key=lambda i: (procs[i].arrival, i))
    ptr = 0
    q = deque()
    slices = []
    t = procs[order[0]].arrival
    left = n

    def admit(upto):
        nonlocal ptr
        while ptr < n and procs[order[ptr]].arrival <= upto:
            q.append(order[ptr])
            ptr += 1

    admit(t)
    while left:
        if not q:
            nxt = procs[order[ptr]].arrival
            slices.append(Slice(None, t, nxt))
            t = nxt
            admit(t)
            continue
        i = q.popleft()
        run = min(quantum, rem[i])
        slices.append(Slice(procs[i].pid, t, t + run))
        t += run
        rem[i] -= run
        admit(t)
        if rem[i] > 0:
            q.append(i)
        else:
            finish[i] = t
            left -= 1
    return slices, finish


def schedule(processes: List[Process], algorithm: str, quantum: Optional[int] = None,
             preemptive: bool = False) -> ScheduleResult:
    algorithm = algorithm.upper()
    validate(processes, algorithm, quantum)
    procs = list(processes)
    if algorithm == "RR":
        slices, finish = _rr_engine(procs, quantum)
    else:
        slices, finish = _priority_engine(procs, algorithm, preemptive)
    slices = _merge(slices)

    first = {}
    for s in slices:
        if s.pid is not None and s.pid not in first:
            first[s.pid] = s.start
    metrics = []
    for p, f in zip(procs, finish):
        tat = f - p.arrival
        metrics.append(ProcMetrics(p.pid, p.arrival, p.burst, first[p.pid], f, tat, tat - p.burst,
                                   first[p.pid] - p.arrival))
    t0 = min(p.arrival for p in procs)
    span = max(finish) - t0
    busy = sum(s.end - s.start for s in slices if s.pid is not None)
    order = []
    for s in slices:
        if s.pid is not None and (not order or order[-1] != s.pid):
            order.append(s.pid)
    n = len(procs)
    return ScheduleResult(
        algorithm=algorithm + (" (preemptive)" if preemptive and algorithm in ("SJF", "PRIORITY") else ""),
        slices=slices, metrics=metrics,
        avg_waiting=sum(m.waiting for m in metrics) / n,
        avg_turnaround=sum(m.turnaround for m in metrics) / n,
        cpu_busy=busy / span if span else 1.0,
        throughput=n / span if span else float(n),
        makespan=span, order=order)
