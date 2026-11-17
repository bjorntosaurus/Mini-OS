import pytest
from algorithms.page_replacement import simulate
from utils.validators import ValidationError

CLASSIC = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1]
DESIGN = [7, 0, 1, 2, 0, 3, 0, 4]


def test_design_example_fifo():
    r = simulate(DESIGN, 3, "FIFO")
    assert (r.faults, r.hits) == (7, 1) and r.hit_ratio == 0.125 and r.fault_ratio == 0.875
    assert r.final_queue == [3, 0, 4]
    last = r.steps[-1]
    assert last.frames == [4, 3, 0] and last.evicted == 2 and last.slot == 0
    assert [s.frames for s in r.steps][:4] == [[7, None, None], [7, 0, None], [7, 0, 1], [2, 0, 1]]


@pytest.mark.parametrize("algo,faults", [("FIFO", 15), ("LRU", 12), ("OPTIMAL", 9)])
def test_classic_string_3_frames(algo, faults):
    r = simulate(CLASSIC, 3, algo)
    assert r.faults == faults and r.faults + r.hits == len(CLASSIC)


def test_belady_anomaly_fifo():
    s = [1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5]
    assert simulate(s, 3, "FIFO").faults == 9 and simulate(s, 4, "FIFO").faults == 10


def test_lru_order_and_one_frame():
    r = simulate([1, 2, 1, 3], 2, "LRU")
    assert r.steps[3].evicted == 2 and r.final_queue == [1, 3]
    assert simulate([1, 1, 1], 1, "FIFO").hits == 2
    assert simulate([1, 2, 1, 2], 1, "OPTIMAL").faults == 4


def test_more_frames_than_pages_and_repeats():
    r = simulate([1, 2, 3, 1, 2, 3], 10, "FIFO")
    assert r.faults == 3 and r.hits == 3


def test_invalid():
    for bad in ((lambda: simulate([], 3, "FIFO")), (lambda: simulate([1], 0, "FIFO")),
                (lambda: simulate([-1], 2, "LRU")), (lambda: simulate([1], 2, "X"))):
        with pytest.raises(ValidationError):
            bad()


def test_large_input_optimal_never_worse():
    import random
    rnd = random.Random(4)
    refs = [rnd.randrange(40) for _ in range(5000)]
    f = {a: simulate(refs, 8, a).faults for a in ("FIFO", "LRU", "OPTIMAL")}
    assert f["OPTIMAL"] <= f["LRU"] and f["OPTIMAL"] <= f["FIFO"]
