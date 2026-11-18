import pytest
from utils.parsers import (parse_matrix, parse_page_table, parse_processes, parse_programs, parse_segments, parse_vector, split_rows)
from utils.validators import ValidationError


def test_split_rows_handles_excel_paste_comments_and_blanks():
    assert split_rows("P1\t0\t5\n\n# note\nP2, 1, 3  # trailing") == [(1, ["P1", "0", "5"]), (4, ["P2", "1", "3"])]


def test_processes_with_ids_priorities_header_and_auto_ids():
    assert parse_processes("PID Arrival Burst\nP1 0 5\nP2,1,3,2") == [("P1", 0, 5, 0), ("P2", 1, 3, 2)]
    assert parse_processes("0 5\n1 3") == [("P1", 0, 5, 0), ("P2", 1, 3, 0)]        # ids generated
    assert len(parse_processes("\n".join(f"P{i} {i} {i % 7 + 1}" for i in range(2000)))) == 2000


@pytest.mark.parametrize("bad", ["P1 0", "P1 a 5", "P1 0 0", "P1 -1 5", "P1 0 5\nP1 1 2", "P1 0 5 6 7"])
def test_processes_errors(bad):
    with pytest.raises(ValidationError):
        parse_processes(bad)


def test_error_names_the_line():
    with pytest.raises(ValidationError, match="Line 2"):
        parse_processes("P1 0 5\nP2 x 3")


def test_vectors_and_matrices():
    assert parse_vector("3 3 2", "Available") == [3, 3, 2]
    assert parse_matrix("0 1 0\n2,0,0\n3\t0\t2", "Allocation") == [[0, 1, 0], [2, 0, 0], [3, 0, 2]]
    for bad in ("1 2\n3", "1 x"):
        with pytest.raises(ValidationError):
            parse_matrix(bad, "M")
    with pytest.raises(ValidationError):
        parse_vector("", "Available")


def test_page_table_formats():
    assert parse_page_table("3 1 5 2 -") == [(3, True), (1, True), (5, True), (2, True), (None, False)]
    assert parse_page_table("0:3, 1:1, 4:-") == [(3, True), (1, True), (None, False), (None, False), (None, False)]
    assert parse_page_table("") == []
    with pytest.raises(ValidationError):
        parse_page_table("3 foo")


def test_segments_formats():
    s = parse_segments("seg base limit\n0 Code 1000 600 rx\n1 2400 400\n2 Stack 4000 800")
    assert [(x.seg_id, x.name, x.base, x.limit, x.perms) for x in s] == [
        (0, "Code", 1000, 600, "READ / EXECUTE"), (1, "", 2400, 400, "READ / WRITE"), (2, "Stack", 4000, 800, "READ / WRITE")]
    with pytest.raises(ValidationError):
        parse_segments("0 Code 1000 600 zz")
    with pytest.raises(ValidationError):
        parse_segments("0 1000")


def test_programs():
    p = parse_programs("name mem cpu io\nP1 128 25 80%\nP2 256 10 50 2 3")
    assert (p[0].name, p[0].memory, p[0].io_wait, p[0].resources) == ("P1", 128, 0.8, 0)
    assert (p[1].resources, p[1].arrival) == (2, 3)
    with pytest.raises(ValidationError):
        parse_programs("P1 128 25 100")                  # I/O wait must be < 100 %
    with pytest.raises(ValidationError):
        parse_programs("P1 128 25 10\nP1 64 5 10")
