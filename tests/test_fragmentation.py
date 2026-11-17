import pytest
from algorithms.fragmentation import allocate
from utils.validators import ValidationError


def test_design_example_internal():
    r = allocate([256] * 4, [212, 180, 96, 64], "first", "fixed")
    assert [b.internal for b in r.blocks] == [44, 76, 160, 192]
    assert r.internal == 472 and r.used == 552 and r.total_memory == 1024 and r.external == 0
    assert round(r.internal / r.total_memory, 3) == 0.461


def test_strategies_classic():
    blocks, procs = [100, 500, 200, 300, 600], [212, 417, 112, 426]
    assert allocate(blocks, procs, "first").assignment == [1, 4, 2, None]
    assert allocate(blocks, procs, "best").assignment == [3, 1, 2, 4]
    assert allocate(blocks, procs, "worst").assignment == [4, 1, 3, None]
    assert allocate(blocks, procs, "next").assignment == [1, 4, 2, None]


def test_external_fragmentation_detected():
    r = allocate([100, 100, 100], [60, 250, 60, 60], "first", "fixed")
    assert r.unallocated == [1] and r.free_total == 0
    r = allocate([50, 50, 50], [60], "first", "fixed")
    assert r.unallocated == [0] and r.external == 150 and r.largest_free == 50


def test_dynamic_mode_splits_holes():
    r = allocate([100, 50], [30, 30, 30, 45], "first", "dynamic")
    assert r.assignment == [0, 0, 0, 1] and r.internal == 0
    assert r.free_total == 15 and [b.free for b in r.blocks] == [10, 5]
    r = allocate([100, 50], [30, 30, 30, 45, 40], "first", "dynamic")
    assert r.unallocated == [4] and r.free_total == 15 and r.external == 0     # 40 > 15 free: not fragmentation


def test_next_fit_continues_from_last():
    r = allocate([10, 10, 10], [5, 5, 5], "next", "dynamic")
    assert r.assignment == [0, 0, 1]      # keeps filling block 0 until it no longer fits
    r = allocate([10, 10, 10], [10, 10, 10], "next", "fixed")
    assert r.assignment == [0, 1, 2]


def test_invalid():
    for args in (([], [1]), ([1], []), ([0], [1]), ([5], [-1])):
        with pytest.raises(ValidationError):
            allocate(*args)
    with pytest.raises(ValidationError):
        allocate([5], [1], "zzz")


def test_large():
    r = allocate([100] * 1000, [(i % 90) + 1 for i in range(1000)], "best")
    assert not r.unallocated and r.used + r.internal == sum(b.size for b in r.blocks if b.processes)
