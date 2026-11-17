import pytest
from algorithms.disk_scheduling import schedule
from utils.validators import ValidationError

Q = [98, 183, 37, 122, 14, 124, 65, 67]


@pytest.mark.parametrize("algo,total", [("FCFS", 640), ("SSTF", 236), ("SCAN", 331), ("CSCAN", 382),
                                        ("LOOK", 299), ("CLOOK", 322)])
def test_textbook_totals_head_53_up(algo, total):
    r = schedule(algo, 53, Q, 0, 199, "up")
    assert r.total == total and sum(r.seeks) == total and sorted(r.order) == sorted(Q)


def test_fcfs_design_ledger():
    r = schedule("FCFS", 53, Q)
    assert r.seeks == [45, 85, 146, 85, 108, 110, 59, 2] and r.average == 80.0


def test_scan_goes_to_boundary_look_does_not():
    assert 199 in schedule("SCAN", 53, Q).path and 199 not in schedule("LOOK", 53, Q).path
    assert 0 in schedule("SCAN", 53, Q, direction="down").path
    assert 0 not in schedule("LOOK", 53, Q, direction="down").path


def test_down_direction():
    assert schedule("SCAN", 53, Q, direction="down").total == 53 + 183
    r = schedule("CSCAN", 53, Q, direction="down")
    assert r.order == [37, 14, 183, 124, 122, 98, 67, 65]
    assert r.total == 53 + 199 + (199 - 65)
    assert schedule("CLOOK", 53, Q, direction="down").order == [37, 14, 183, 124, 122, 98, 67, 65]


def test_cscan_return_jump_optional():
    assert schedule("CSCAN", 53, Q, count_return=False).total == 382 - 199
    assert schedule("CLOOK", 53, Q, count_return=False).total == 322 - 169


def test_edge_cases():
    r = schedule("SCAN", 50, [50], 0, 99)
    assert r.order == [50] and r.total == 49       # SCAN still sweeps to the boundary
    assert schedule("FCFS", 5, [5, 5]).total == 0
    assert schedule("SSTF", 0, [0, 199]).total == 199
    assert schedule("LOOK", 100, [10, 20]).total == 90
    assert schedule("CLOOK", 100, [10, 20]).order == [10, 20]


def test_invalid():
    for call in (lambda: schedule("FCFS", 5, []), lambda: schedule("FCFS", 500, [1]),
                 lambda: schedule("FCFS", 5, [1, 999]), lambda: schedule("FCFS", 5, [1], 10, 10),
                 lambda: schedule("XYZ", 5, [1]), lambda: schedule("SCAN", 5, [1], direction="left")):
        with pytest.raises(ValidationError):
            call()


def test_large_queue():
    import random
    rnd = random.Random(9)
    reqs = [rnd.randrange(0, 5000) for _ in range(3000)]
    t = {a: schedule(a, 2500, reqs, 0, 4999).total for a in ("FCFS", "SSTF", "SCAN", "LOOK")}
    assert t["SSTF"] < t["FCFS"] and t["LOOK"] <= t["SCAN"]
