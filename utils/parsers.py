"""Bulk-input parsers: turn pasted / typed text tables into validated data.

Accepted separators: commas, tabs, semicolons and spaces (so a block copied from Excel / a PDF / a textbook just works).
Blank lines and everything after '#' are ignored.  A first line that looks like a header (e.g. 'PID Arrival Burst') is skipped.
Every error message names the offending line number."""
import re
from typing import List, Optional, Tuple

from models.records import Program, Segment
from utils.validators import ValidationError, parse_float, parse_int

_INT = re.compile(r"[+-]?\d+$")


def split_rows(text: str) -> List[Tuple[int, List[str]]]:
    """Return [(line_number, [tokens...])] for every non-empty line."""
    rows = []
    for no, line in enumerate(str(text).splitlines(), 1):
        line = line.split("#")[0].strip()
        if line:
            rows.append((no, [t for t in re.split(r"[,\t;\s]+", line) if t]))
    return rows


def _is_int(tok):
    return bool(_INT.match(tok))


def _is_header(no, tokens, first_no):
    """A first line without a single number in it ('PID Arrival Burst') is a header, not data."""
    return no == first_no and not any(_is_int(t.rstrip("%")) for t in tokens)


# ----------------------------------------------------------------------------- CPU scheduling
def parse_processes(text: str, first_auto: int = 1) -> List[Tuple[str, int, int, int]]:
    """Lines: 'P1 0 5'  or  'P1 0 5 2' (id arrival burst [priority]).  Without an id ('0 5') IDs P1, P2... are generated."""
    rows = split_rows(text)
    out, auto = [], first_auto
    for no, t in rows:
        if not _is_int(t[0]):                                   # leading token is a process id
            if _is_header(no, t, rows[0][0]):
                continue
            pid, nums = t[0], t[1:]
        else:
            pid, nums = f"P{auto}", t
            auto += 1
        if len(nums) not in (2, 3):
            raise ValidationError(f"Line {no}: expected 'id arrival burst [priority]', found {len(t)} value(s).")
        arrival = parse_int(nums[0], f"Line {no} arrival time", 0)
        burst = parse_int(nums[1], f"Line {no} burst time", 1)
        prio = parse_int(nums[2], f"Line {no} priority") if len(nums) == 3 else 0
        out.append((pid, arrival, burst, prio))
    if len({p[0] for p in out}) != len(out):
        raise ValidationError("Process IDs must be unique.")
    return out


# ----------------------------------------------------------------------------- Banker's
def parse_vector(text: str, name: str) -> List[int]:
    toks = [t for _, row in split_rows(text) for t in row]
    if not toks:
        raise ValidationError(f"{name}: no numbers entered.")
    return [parse_int(t, name, 0) for t in toks]


def parse_matrix(text: str, name: str) -> List[List[int]]:
    """One process per line, one number per resource. Every line must have the same number of values."""
    rows = split_rows(text)
    out = []
    for no, t in rows:
        out.append([parse_int(x, f"{name} line {no}", 0) for x in t])
    if out and len({len(r) for r in out}) != 1:
        raise ValidationError(f"{name}: all lines must have the same number of values.")
    return out


# ----------------------------------------------------------------------------- Paging
def parse_page_table(text: str) -> List[Tuple[Optional[int], bool]]:
    """One token per page, in page order: a frame number = resident, '-' (or x / n / none) = not resident.
    'page:frame' pairs are accepted too ('0:3 1:1 4:-'); missing pages are filled as not resident."""
    toks = [t for _, row in split_rows(text) for t in row]
    pairs = {}
    seq = 0
    for t in toks:
        if ":" in t or "=" in t:
            pg, fr = re.split(r"[:=]", t, maxsplit=1)
            page = parse_int(pg, "Page number", 0)
        else:
            page, fr = seq, t
        seq = page + 1
        if fr.lower() in ("-", "x", "n", "no", "none", "—", ""):
            pairs[page] = (None, False)
        else:
            pairs[page] = (parse_int(fr, f"Frame of page {page}", 0), True)
    if not pairs:
        return []
    return [pairs.get(p, (None, False)) for p in range(max(pairs) + 1)]


# ----------------------------------------------------------------------------- Segmentation
_PERMS = {"r": "READ ONLY", "ro": "READ ONLY", "rw": "READ / WRITE", "rx": "READ / EXECUTE", "rwx": "READ / WRITE / EXECUTE"}


def parse_segments(text: str) -> List[Segment]:
    """Lines: 'id base limit' | 'id name base limit' | 'id name base limit perms(r|rw|rx|rwx)'."""
    out, rows = [], split_rows(text)
    for no, t in rows:
        if _is_header(no, t, rows[0][0]):
            continue
        if len(t) == 3:
            sid, name, base, limit, perms = t[0], "", t[1], t[2], "rw"
        elif len(t) == 4:
            sid, name, base, limit, perms = t[0], t[1], t[2], t[3], "rw"
        elif len(t) == 5:
            sid, name, base, limit, perms = t
        else:
            raise ValidationError(f"Line {no}: expected 'id [name] base limit [perms]', found {len(t)} value(s).")
        if perms.lower() not in _PERMS:
            raise ValidationError(f"Line {no}: protection '{perms}' must be one of r, rw, rx, rwx.")
        out.append(Segment(parse_int(sid, f"Line {no} segment id", 0), name, parse_int(base, f"Line {no} base", 0),
                           parse_int(limit, f"Line {no} limit", 1), _PERMS[perms.lower()]))
    return out


# ----------------------------------------------------------------------------- Multiprogramming
def parse_programs(text: str) -> List[Program]:
    """Lines: 'name memory_MB cpu_ticks io_wait_% [resource_units] [arrival_tick]'."""
    out, rows = [], split_rows(text)
    for no, t in rows:
        if _is_header(no, t, rows[0][0]):
            continue
        if not 4 <= len(t) <= 6:
            raise ValidationError(f"Line {no}: expected 'name memory cpu io% [resources] [arrival]', found {len(t)} value(s).")
        out.append(Program(t[0], parse_int(t[1], f"Line {no} memory", 1), parse_int(t[2], f"Line {no} CPU time", 1),
                           parse_float(t[3].rstrip("%"), f"Line {no} I/O wait", 0, 99) / 100,
                           parse_int(t[4], f"Line {no} resources", 0) if len(t) > 4 else 0,
                           parse_int(t[5], f"Line {no} arrival", 0) if len(t) > 5 else 0))
    if len({p.name for p in out}) != len(out):
        raise ValidationError("Program names must be unique.")
    return out
