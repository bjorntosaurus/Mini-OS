import pytest
from algorithms.bankers_algorithm import is_safe, need_matrix, request_resources
from utils.validators import ValidationError

AV = [3, 3, 2]
AL = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
MX = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]


def test_need_matrix():
    assert need_matrix(AL, MX) == [[7, 4, 3], [1, 2, 2], [6, 0, 0], [0, 1, 1], [4, 3, 1]]


def test_safe_sequence_and_work_trace():
    r = is_safe(AV, AL, MX)
    assert r.safe and r.sequence == [1, 3, 4, 0, 2]
    assert [s.work_after for s in r.steps] == [(5, 3, 2), (7, 4, 3), (7, 4, 5), (7, 5, 5), (10, 5, 7)]


def test_unsafe_state():
    r = is_safe([0, 0], [[1, 0], [0, 1]], [[2, 1], [1, 2]])
    assert not r.safe and r.sequence == [] and r.unfinished == [0, 1]


def test_partially_safe_reports_unfinished():
    r = is_safe([1], [[0], [1], [1]], [[1], [3], [3]])
    assert not r.safe and r.sequence == [0]


def test_request_granted_and_denied():
    assert request_resources(1, [1, 0, 2], AV, AL, MX).granted
    av2, al2 = [2, 3, 0], [[0, 1, 0], [3, 0, 2], [3, 0, 2], [2, 1, 1], [0, 0, 2]]   # after P1's grant
    r = request_resources(0, [0, 2, 0], av2, al2, MX)
    assert not r.granted and "UNSAFE" in r.reason
    assert "not available" in request_resources(4, [3, 3, 0], av2, al2, MX).reason
    assert "maximum" in request_resources(1, [9, 0, 0], AV, AL, MX).reason


def test_single_resource_and_zero_available():
    r = is_safe([0], [[1]], [[1]])
    assert r.safe and r.sequence == [0]


def test_invalid():
    with pytest.raises(ValidationError):
        is_safe([], [], [])
    with pytest.raises(ValidationError):
        is_safe([1], [[2]], [[1]])                       # allocation > maximum
    with pytest.raises(ValidationError):
        is_safe([1, 1], [[1]], [[1, 1]])                 # ragged
    with pytest.raises(ValidationError):
        is_safe([-1], [[0]], [[1]])
    with pytest.raises(ValidationError):
        request_resources(7, [0, 0, 0], AV, AL, MX)


def test_large_system():
    n, m = 300, 6
    al = [[0] * m for _ in range(n)]
    mx = [[1] * m for _ in range(n)]
    r = is_safe([1] * m, al, mx)
    assert r.safe and len(r.sequence) == n
