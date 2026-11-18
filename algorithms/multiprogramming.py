"""Multiprogramming: the classic CPU-utilisation model  U = 1 - p^n  plus a tick-based
simulation of programs sharing memory, a pool of resource units and one CPU.

Simulation rules (one tick = one time unit):
 1. Programs that have arrived are admitted to memory in queue order when their memory
    (and resource units) fit.  Programs that do not fit stay QUEUED (state 'Q').
 2. Every resident program is blocked on I/O in a tick with probability io_wait
    (seeded RNG -> reproducible).  Others are READY ('Y').
 3. The CPU runs one READY program (round robin, `quantum` ticks) -> state 'R'.
 4. A program that has received cpu_time ticks completes ('D'); memory and resources
    are released at the end of that tick.
States: '-' not arrived, 'Q' queued, 'Y' ready, 'R' running, 'W' waiting for I/O, 'D' done."""
import random
from typing import List, Optional

from models.records import Program, SimResult
from utils.validators import ValidationError


# Classic model: if each of n resident programs waits for I/O with probability p (independently), the CPU is idle
# only when ALL n wait, i.e. with probability p**n.  Utilisation = 1 - p**n.
def cpu_utilization(n: int, p: float) -> float:
    """Return 1 - p**n for n resident programs with I/O-wait probability p (0 <= p <= 1, n >= 0)."""
    if n < 0:
        raise ValidationError("Degree of multiprogramming cannot be negative.")
    if not 0.0 <= p <= 1.0:
        raise ValidationError("I/O wait probability must be between 0 and 1.")
    return 1.0 - p ** n


def utilization_curve(max_n: int, p: float):
    """Return [U(1), U(2), ..., U(max_n)] for the given p (used to draw the 'more programs, less idle time' curve)."""
    if max_n < 1:
        raise ValidationError("The curve needs at least one point.")
    return [cpu_utilization(n, p) for n in range(1, max_n + 1)]


# Reject programs that could never run (bigger than the machine, zero CPU time, I/O probability outside [0,1), ...).
def validate(programs: List[Program], total_memory: int, total_resources: Optional[int]):
    """Raise ValidationError if the program list / system sizes are impossible (see the module docstring)."""
    if not programs:
        raise ValidationError("Add at least one program.")
    if total_memory < 1:
        raise ValidationError("Total memory must be at least 1 MB.")
    names = set()
    for p in programs:
        if p.name in names:
            raise ValidationError(f"Duplicate program name '{p.name}'.")
        names.add(p.name)
        if p.memory < 1:
            raise ValidationError(f"{p.name}: memory requirement must be at least 1 MB.")
        if p.memory > total_memory:
            raise ValidationError(f"{p.name}: needs {p.memory} MB but the system only has {total_memory} MB.")
        if p.cpu_time < 1:
            raise ValidationError(f"{p.name}: CPU time must be at least 1.")
        if not 0.0 <= p.io_wait < 1.0:
            raise ValidationError(f"{p.name}: I/O wait must be from 0% up to (not including) 100%.")
        if p.arrival < 0:
            raise ValidationError(f"{p.name}: arrival cannot be negative.")
        if p.resources < 0:
            raise ValidationError(f"{p.name}: resource units cannot be negative.")
        if total_resources is not None and p.resources > total_resources:
            raise ValidationError(f"{p.name}: needs {p.resources} resource units but only {total_resources} exist.")


def simulate(programs: List[Program], total_memory: int, total_resources: Optional[int] = None,
             seed: int = 1, quantum: int = 1) -> SimResult:
    """Run the tick-based multiprogramming simulation.

    Args:
        programs: list of Program(name, memory, cpu_time, io_wait, resources, arrival).
        total_memory: machine memory; total_resources: resource units (None = unlimited).
        seed: RNG seed; quantum: round-robin time slice in ticks.
    Returns:
        SimResult with a per-program state string (one character per tick), memory/resource usage per tick,
        admission/finish times and the summary statistics.
    """
    validate(programs, total_memory, total_resources)
    if quantum < 1:
        raise ValidationError("Quantum must be at least 1.")
    # Seeded RNG -> the same input and seed always produce the same simulation (reproducible, testable).
    rng = random.Random(seed)
    n = len(programs)
    # cpu_left = CPU ticks still needed; admitted/finish = tick numbers; resident = currently holds memory.
    # mem / res = memory and resource units currently in use. last/used_q implement the round-robin quantum.
    cpu_left = [p.cpu_time for p in programs]
    admitted = [None] * n
    finish = [None] * n
    resident = [False] * n
    states = [[] for _ in range(n)]
    mem_hist, res_hist, busy_hist, degree_hist = [], [], [], []
    mem = res = 0
    last, used_q = -1, 0
    t = 0
    # One loop iteration = one clock tick, repeated until every program has finished.
    while any(f is None for f in finish):
        # STEP 1 - ADMISSION (job scheduler): an arrived program becomes resident only if its memory (and resource units) fit;
        # otherwise it stays QUEUED.
        for i, p in enumerate(programs):                       # admission
            if admitted[i] is None and p.arrival <= t:
                if mem + p.memory <= total_memory and (total_resources is None or res + p.resources <= total_resources):
                    admitted[i] = t
                    resident[i] = True
                    mem += p.memory
                    res += p.resources
        # STEP 2 - STATES: classify every program this tick:
        #   '-' not arrived, 'D' done, 'Q' queued (no room), 'W' blocked on I/O (random draw < io_wait), 'Y' ready.
        tick = ["-"] * n
        ready = []
        for i, p in enumerate(programs):
            if finish[i] is not None:
                tick[i] = "D"
            elif p.arrival > t:
                tick[i] = "-"
            elif not resident[i]:
                tick[i] = "Q"
            elif rng.random() < p.io_wait:
                tick[i] = "W"
            else:
                tick[i] = "Y"
                ready.append(i)
        # STEP 3 - CPU (round robin): keep running the same program until its quantum is used up, otherwise take the next
        # ready program after it (wrapping). The chosen one becomes 'R' and consumes one CPU tick.
        run = None
        if ready:
            if last in ready and used_q < quantum:
                run = last
            else:
                after = [i for i in ready if i > last]
                run = after[0] if after else ready[0]
                used_q = 0
            used_q += 1
            last = run
            tick[run] = "R"
            cpu_left[run] -= 1
        else:
            last, used_q = -1, 0
        # STEP 4 - BOOKKEEPING for charts/statistics: memory, resource units, CPU busy flag and degree of multiprogramming.
        mem_hist.append(mem)
        res_hist.append(res)
        busy_hist.append(run is not None)
        degree_hist.append(sum(resident))
        for i in range(n):
            states[i].append(tick[i])
        # STEP 5 - COMPLETION: a program that got all its CPU time leaves; its memory and resource units are freed at the end of the tick.
        if run is not None and cpu_left[run] == 0:
            finish[run] = t + 1
            resident[run] = False
            mem -= programs[run].memory
            res -= programs[run].resources
            last, used_q = -1, 0
        t += 1
        if t > 5_000_000:
            raise ValidationError("Simulation did not terminate (check the input).")
    # Summary statistics: CPU utilisation = busy ticks / total ticks, average memory use, peak memory,
    # maximum number of resident programs and average turnaround (finish - arrival).
    ticks = t
    return SimResult(["".join(s) for s in states], mem_hist, res_hist, busy_hist, admitted, finish, ticks,
                     sum(busy_hist) / ticks, sum(mem_hist) / ticks / total_memory, max(mem_hist),
                     max(degree_hist), sum(f - p.arrival for f, p in zip(finish, programs)) / n)
