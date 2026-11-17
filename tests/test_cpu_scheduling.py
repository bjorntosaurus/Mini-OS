import pytest
from algorithms.cpu_scheduling import schedule
from models.records import Process
from utils.validators import ValidationError

FIG = [Process("P1", 0, 5), Process("P2", 1, 3), Process("P3", 2, 1), Process("P4", 3, 2)]


def by(res):
    return {m.pid: m for m in res.metrics}


def test_fcfs_matches_design_example():
    r = schedule(FIG, "FCFS")
    m = by(r)
    assert [(m[p].start, m[p].finish, m[p].waiting, m[p].turnaround) for p in ("P1", "P2", "P3", "P4")] == \
        [(0, 5, 0, 5), (5, 8, 4, 7), (8, 9, 6, 7), (9, 11, 6, 8)]
    assert r.avg_waiting == 4.0 and r.avg_turnaround == 6.75
    assert r.cpu_busy == 1.0 and round(r.throughput, 2) == 0.36
    assert r.order == ["P1", "P2", "P3", "P4"]


def test_sjf_non_preemptive():
    r = schedule(FIG, "SJF")
    assert r.order == ["P1", "P3", "P4", "P2"]
    assert r.avg_waiting == 3.25 and r.avg_turnaround == 6.0


def test_srtf_preemptive_textbook():
    ps = [Process("P1", 0, 8), Process("P2", 1, 4), Process("P3", 2, 9), Process("P4", 3, 5)]
    r = schedule(ps, "SJF", preemptive=True)
    assert r.avg_waiting == 6.5
    assert [(s.pid, s.start, s.end) for s in r.slices][:3] == [("P1", 0, 1), ("P2", 1, 5), ("P4", 5, 10)]


def test_priority_non_preemptive_textbook():
    ps = [Process("P1", 0, 10, 3), Process("P2", 0, 1, 1), Process("P3", 0, 2, 4),
          Process("P4", 0, 1, 5), Process("P5", 0, 5, 2)]
    r = schedule(ps, "PRIORITY")
    assert r.order == ["P2", "P5", "P1", "P3", "P4"] and r.avg_waiting == 8.2


def test_priority_preemptive():
    ps = [Process("A", 0, 5, 3), Process("B", 1, 2, 1)]
    r = schedule(ps, "PRIORITY", preemptive=True)
    assert [(s.pid, s.start, s.end) for s in r.slices] == [("A", 0, 1), ("B", 1, 3), ("A", 3, 7)]


def test_round_robin_textbook():
    ps = [Process("P1", 0, 24), Process("P2", 0, 3), Process("P3", 0, 3)]
    r = schedule(ps, "RR", quantum=4)
    m = by(r)
    assert (m["P1"].waiting, m["P2"].waiting, m["P3"].waiting) == (6, 4, 7)


def test_round_robin_arrival_goes_before_preempted():
    ps = [Process("A", 0, 4), Process("B", 1, 1)]
    r = schedule(ps, "RR", quantum=2)
    assert r.order == ["A", "B", "A"]


def test_idle_gap_and_late_start():
    r = schedule([Process("A", 0, 2), Process("B", 5, 1)], "FCFS")
    assert [(s.pid, s.start, s.end) for s in r.slices] == [("A", 0, 2), (None, 2, 5), ("B", 5, 6)]
    assert round(r.cpu_busy, 3) == 0.5
    r = schedule([Process("A", 10, 2)], "FCFS")
    assert r.metrics[0].start == 10 and r.metrics[0].waiting == 0


def test_tie_breaking_input_order():
    r = schedule([Process("A", 0, 3), Process("B", 0, 3)], "SJF")
    assert r.order == ["A", "B"]


@pytest.mark.parametrize("algo", ["FCFS", "SJF", "PRIORITY", "RR"])
def test_single_process(algo):
    r = schedule([Process("X", 2, 4, 1)], algo, quantum=3)
    assert r.metrics[0].finish == 6 and r.metrics[0].waiting == 0


def test_invalid_inputs():
    with pytest.raises(ValidationError):
        schedule([], "FCFS")
    with pytest.raises(ValidationError):
        schedule([Process("A", 0, 0)], "FCFS")
    with pytest.raises(ValidationError):
        schedule([Process("A", -1, 2)], "FCFS")
    with pytest.raises(ValidationError):
        schedule([Process("A", 0, 2), Process("A", 1, 2)], "FCFS")
    with pytest.raises(ValidationError):
        schedule([Process("A", 0, 2)], "RR", quantum=0)
    with pytest.raises(ValidationError):
        schedule([Process("A", 0, 2)], "NOPE")


def test_large_dataset_invariants():
    ps = [Process(f"P{i}", i % 50, 1 + (i * 7) % 13, i % 5) for i in range(600)]
    for algo, kw in [("FCFS", {}), ("SJF", {}), ("SJF", {"preemptive": True}), ("PRIORITY", {}), ("RR", {"quantum": 3})]:
        r = schedule(ps, algo, **kw)
        assert sum(s.end - s.start for s in r.slices if s.pid) == sum(p.burst for p in ps)
        assert all(m.turnaround == m.waiting + m.burst and m.waiting >= 0 for m in r.metrics)
