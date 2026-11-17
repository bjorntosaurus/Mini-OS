import math
import pytest
from algorithms.multiprogramming import cpu_utilization, utilization_curve, simulate
from models.records import Program
from utils.validators import ValidationError


def test_model_matches_design():
    assert round(cpu_utilization(4, 0.8) * 100, 2) == 59.04
    assert cpu_utilization(0, 0.5) == 0 and cpu_utilization(3, 0) == 1 and cpu_utilization(3, 1) == 0
    c = utilization_curve(8, 0.8)
    assert len(c) == 8 and all(a < b for a, b in zip(c, c[1:]))


def test_model_invalid():
    for call in (lambda: cpu_utilization(-1, .5), lambda: cpu_utilization(1, 1.5), lambda: utilization_curve(0, .5)):
        with pytest.raises(ValidationError):
            call()


def test_simulation_no_io_is_sequential_round_robin():
    ps = [Program("A", 100, 3, 0.0), Program("B", 100, 2, 0.0)]
    r = simulate(ps, 1024)
    assert r.ticks == 5 and r.cpu_utilization == 1.0 and r.finish == [5, 4]
    assert r.states[0].count("R") == 3 and r.states[1].count("R") == 2


def test_memory_limits_force_queueing():
    ps = [Program("A", 600, 2, 0.0), Program("B", 600, 2, 0.0)]
    r = simulate(ps, 1024)
    assert r.admitted_at == [0, 2] and r.max_degree == 1 and r.states[1].startswith("QQ")
    assert r.peak_memory == 600 and r.finish == [2, 4]


def test_resource_units_limit_admission():
    ps = [Program("A", 10, 2, 0.0, resources=3), Program("B", 10, 2, 0.0, resources=3)]
    r = simulate(ps, 1024, total_resources=4)
    assert r.admitted_at[1] == 2 and r.res_used[0] == 3


def test_arrival_and_states():
    r = simulate([Program("A", 10, 1, 0.0, arrival=3)], 100)
    assert r.states[0] == "---R" and r.finish == [4]


def test_reproducible_and_close_to_model():
    ps = [Program(f"P{i}", 128, 400, 0.8) for i in range(4)]
    a, b = simulate(ps, 1024, seed=5), simulate(ps, 1024, seed=5)
    assert a.states == b.states
    assert abs(a.cpu_utilization - cpu_utilization(4, 0.8)) < 0.08
    for s in a.states:
        assert set(s) <= set("-QYRWD")


def test_invalid_and_large():
    for ps, mem in (([], 100), ([Program("A", 200, 1)], 100), ([Program("A", 1, 0)], 10),
                    ([Program("A", 1, 1, 1.0)], 10), ([Program("A", 1, 1), Program("A", 1, 1)], 10),
                    ([Program("A", 1, 1)], 0)):
        with pytest.raises(ValidationError):
            simulate(ps, mem)
    big = [Program(f"P{i}", 10 + i % 40, 5 + i % 7, 0.3, resources=i % 3) for i in range(300)]
    r = simulate(big, 1024, total_resources=20)
    assert all(f is not None for f in r.finish) and max(r.mem_used) <= 1024
