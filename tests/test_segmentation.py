import pytest
from algorithms.segmentation import translate, validate_table, gaps
from models.records import Segment
from utils.validators import ValidationError

SEGS = [Segment(0, "Code", 1000, 600), Segment(1, "Data", 2400, 400), Segment(2, "Stack", 4000, 800),
        Segment(3, "Heap", 5600, 1200)]


def test_valid_translation():
    r = translate(SEGS, 0, 240)
    assert r.valid and r.physical == 1240


def test_limit_boundaries():
    assert translate(SEGS, 0, 599).physical == 1599
    r = translate(SEGS, 0, 600)
    assert not r.valid and "limit" in r.message
    assert translate(SEGS, 0, 0).physical == 1000


def test_bad_segment_and_offset():
    assert not translate(SEGS, 9, 1).valid
    assert not translate(SEGS, 1, -3).valid


def test_table_validation():
    with pytest.raises(ValidationError):
        validate_table([])
    with pytest.raises(ValidationError):
        validate_table([Segment(0, "a", 0, 10), Segment(0, "b", 20, 10)])
    with pytest.raises(ValidationError):
        validate_table([Segment(0, "a", 0, 10), Segment(1, "b", 5, 10)])      # overlap
    with pytest.raises(ValidationError):
        validate_table([Segment(0, "a", 0, 0)])
    with pytest.raises(ValidationError):
        validate_table([Segment(0, "a", -1, 4)])
    with pytest.raises(ValidationError):
        validate_table([Segment(0, "a", 90, 20)], memory_size=100)


def test_adjacent_segments_allowed_and_gaps():
    validate_table([Segment(0, "a", 0, 10), Segment(1, "b", 10, 10)])
    assert gaps(SEGS, 6800) == [(0, 1000), (1600, 2400), (2800, 4000), (4800, 5600)]
    assert gaps(SEGS, 7000)[-1] == (6800, 7000)


def test_many_segments():
    segs = [Segment(i, f"s{i}", i * 100, 100) for i in range(2000)]
    assert translate(segs, 1999, 99).physical == 199999
