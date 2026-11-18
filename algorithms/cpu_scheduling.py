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


# Input checks shared by every scheduling policy (raises ValidationError with a readable message).
def validate(processes: List[Process], algorithm: str, quantum: Optional[int]):
    """Raise ValidationError for any input that makes scheduling meaningless (empty list, duplicate IDs, bad times, bad quantum)."""
    if algorithm not in ALGORITHMS:
        raise ValidationError(f"Unknown algorithm '{algorithm}'.")
    if not processes:
        raise ValidationError("Add at least one process before running the queue.")
    # Process IDs must be unique, non-empty; arrival >= 0 and burst >= 1 (a 0-length burst would never run).
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
    # Round Robin additionally needs a positive time quantum.
    if algorithm == "RR" and (quantum is None or quantum < 1):
        raise ValidationError("Round Robin needs a time quantum of at least 1.")


# Glue back-to-back slices of the same process into one Gantt block (P1 0-2 + P1 2-5 -> P1 0-5).
def _merge(slices):
    """Return the slices with adjacent blocks of the same process merged and empty blocks dropped."""
    out = []
    for s in slices:
        if s.end <= s.start:
            continue
        if out and out[-1].pid == s.pid and out[-1].end == s.start:
            out[-1].end = s.end
        else:
            out.append(Slice(s.pid, s.start, s.end))
    return out


# Event-driven engine for FCFS, SJF/SRTF and Priority.
# Each loop iteration picks ONE process (lowest `key`) among those that have arrived and runs it either to completion
# (non-preemptive) or until the next arrival, when the choice is re-evaluated (preemptive).
def _priority_engine(procs, algorithm, preemptive):
    """Simulate FCFS / SJF / Priority.

    Returns (slices, finish) where finish[i] is the completion time of procs[i].
    """
    n = len(procs)
    # rem[i] = CPU time process i still needs; done[i]/finish[i] track completion; slices is the Gantt chart.
    rem = [p.burst for p in procs]
    done = [False] * n
    finish = [0] * n
    slices = []
    # The clock starts when the first process arrives (no idle block before it).
    t = min(p.arrival for p in procs)
    left = n

    # Sort key = the scheduling policy. Lower tuple wins; later tuple entries are tie-breakers
    # (earlier arrival first, then input order), so results are deterministic.
    def key(i):
        p = procs[i]
        if algorithm == "FCFS":
            return (p.arrival, i)
        if algorithm == "SJF":
            return ((rem[i] if preemptive else p.burst), p.arrival, i)
        return (p.priority, p.arrival, i)

    while left:
        # Ready queue = processes that have already arrived and are not finished.
        ready = [i for i in range(n) if not done[i] and procs[i].arrival <= t]
        # CPU idle: nobody has arrived yet. Jump the clock to the next arrival and record an idle slice (pid=None).
        if not ready:
            nxt = min(procs[i].arrival for i in range(n) if not done[i])
            slices.append(Slice(None, t, nxt))
            t = nxt
            continue
        # Dispatch: the policy decides who gets the CPU.
        i = min(ready, key=key)
        # Non-preemptive default: run to completion.
        run = rem[i]
        # Preemptive (SRTF / preemptive Priority): only run until the next arrival, then choose again
        # (a newcomer with a shorter remaining time / better priority takes over).
        if preemptive and algorithm != "FCFS":
            arrivals = [procs[j].arrival for j in range(n) if not done[j] and procs[j].arrival > t]
            if arrivals:
                run = min(run, min(arrivals) - t)
        # Record the Gantt block, advance the clock, charge the CPU time to the process.
        slices.append(Slice(procs[i].pid, t, t + run))
        t += run
        rem[i] -= run
        if rem[i] == 0:
            done[i] = True
            finish[i] = t
            left -= 1
    return slices, finish


# Round Robin: processes take turns of at most `quantum` time units from a FIFO ready queue.
def _rr_engine(procs, quantum):
    """Simulate Round Robin with the given quantum.

    Returns (slices, finish) like _priority_engine.
    """
    n = len(procs)
    rem = [p.burst for p in procs]
    finish = [0] * n
    # Arrival order (ties by input order); ptr marks the next process that has not entered the queue yet.
    order = sorted(range(n), key=lambda i: (procs[i].arrival, i))
    ptr = 0
    q = deque()
    slices = []
    t = procs[order[0]].arrival
    left = n

    # Move every process that has arrived by time `upto` into the ready queue.
    def admit(upto):
        nonlocal ptr
        while ptr < n and procs[order[ptr]].arrival <= upto:
            q.append(order[ptr])
            ptr += 1

    admit(t)
    while left:
        # Queue empty but work remains: CPU idles until the next arrival.
        if not q:
            nxt = procs[order[ptr]].arrival
            slices.append(Slice(None, t, nxt))
            t = nxt
            admit(t)
            continue
        # Take the head of the queue and run it for min(quantum, remaining) units.
        i = q.popleft()
        run = min(quantum, rem[i])
        slices.append(Slice(procs[i].pid, t, t + run))
        t += run
        rem[i] -= run
        admit(t)
        # Convention: processes that arrived DURING this slice are queued first, then the pre-empted process goes to the back.
        if rem[i] > 0:
            q.append(i)
        else:
            finish[i] = t
            left -= 1
    return slices, finish


# Public entry point: validate, run the chosen engine, then derive every metric from the finish times.
def schedule(processes: List[Process], algorithm: str, quantum: Optional[int] = None,
             preemptive: bool = False) -> ScheduleResult:
    """Run one scheduling algorithm.

    Args:
        processes: list of Process(pid, arrival, burst, priority); order matters for tie-breaking.
        algorithm: 'FCFS', 'SJF', 'PRIORITY' or 'RR'.
        quantum: time slice for RR (ignored otherwise).
        preemptive: only affects SJF (-> SRTF) and PRIORITY.
    Returns:
        ScheduleResult with the Gantt slices, per-process metrics, averages, CPU-busy % and throughput.
    Raises:
        ValidationError on invalid input.
    """
    algorithm = algorithm.upper()
    validate(processes, algorithm, quantum)
    procs = list(processes)
    if algorithm == "RR":
        slices, finish = _rr_engine(procs, quantum)
    else:
        slices, finish = _priority_engine(procs, algorithm, preemptive)
    slices = _merge(slices)

    # Start time = first moment a process touches the CPU (needed for response time).
    first = {}
    for s in slices:
        if s.pid is not None and s.pid not in first:
            first[s.pid] = s.start
    metrics = []
    # Per-process metrics:  turnaround = completion - arrival;  waiting = turnaround - burst;  response = first start - arrival.
    for p, f in zip(procs, finish):
        tat = f - p.arrival
        metrics.append(ProcMetrics(p.pid, p.arrival, p.burst, first[p.pid], f, tat, tat - p.burst,
                                   first[p.pid] - p.arrival))
    # System-level metrics use the span from the first arrival to the last completion:
    # cpu_busy = busy time / span,  throughput = processes / span.
    t0 = min(p.arrival for p in procs)
    span = max(finish) - t0
    busy = sum(s.end - s.start for s in slices if s.pid is not None)
    # Execution order = sequence of distinct consecutive pids in the Gantt chart (idle blocks skipped).
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
