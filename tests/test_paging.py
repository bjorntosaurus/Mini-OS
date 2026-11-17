import pytest
from algorithms.paging import translate, frame_map
from utils.validators import ValidationError

T = [(3, True), (1, True), (5, True), (2, True), (None, False)]


def test_design_example():
    r = translate(2172, 1024, T, 6)
    assert (r.status, r.page, r.offset, r.frame, r.physical) == ("ok", 2, 124, 5, 5244)


def test_boundaries():
    assert translate(0, 1024, T, 6).physical == 3 * 1024
    assert translate(1023, 1024, T, 6).physical == 3 * 1024 + 1023
    assert translate(1024, 1024, T, 6).physical == 1024


def test_page_fault_and_invalid():
    assert translate(4 * 1024 + 5, 1024, T, 6).status == "page_fault"
    r = translate(5 * 1024, 1024, T, 6)
    assert r.status == "invalid" and "outside" in r.message


def test_frame_map():
    assert frame_map(T, 6) == [None, 1, 3, 0, None, 2]


def test_invalid_configuration():
    with pytest.raises(ValidationError):
        translate(-1, 1024, T, 6)
    with pytest.raises(ValidationError):
        translate(1, 0, T, 6)
    with pytest.raises(ValidationError):
        translate(1, 1024, [], 6)
    with pytest.raises(ValidationError):
        translate(1, 1024, [(9, True)], 6)                # frame beyond memory
    with pytest.raises(ValidationError):
        translate(1, 1024, [(1, True), (1, True)], 6)     # duplicate frame
    with pytest.raises(ValidationError):
        translate(1, 1024, [(None, True)], 6)
    with pytest.raises(ValidationError):
        translate(1, 1024, T, 0)


def test_large_table():
    table = [(i, True) for i in range(5000)]
    assert translate(4999 * 256 + 7, 256, table, 5000).physical == 4999 * 256 + 7
