"""Segmentation: segment table validation and base/limit address translation."""
from typing import List, Optional

from models.records import Segment, SegTranslation
from utils.validators import ValidationError


def validate_table(segments: List[Segment], memory_size: Optional[int] = None):
    if not segments:
        raise ValidationError("The segment table is empty. Add at least one segment.")
    ids = set()
    for s in segments:
        if s.seg_id < 0:
            raise ValidationError("Segment IDs cannot be negative.")
        if s.seg_id in ids:
            raise ValidationError(f"Duplicate segment ID {s.seg_id}.")
        ids.add(s.seg_id)
        if s.base < 0:
            raise ValidationError(f"Segment {s.seg_id}: base address cannot be negative.")
        if s.limit < 1:
            raise ValidationError(f"Segment {s.seg_id}: limit must be at least 1.")
        if memory_size is not None and s.base + s.limit > memory_size:
            raise ValidationError(f"Segment {s.seg_id} ends at {s.base + s.limit}, beyond physical memory ({memory_size}).")
    ordered = sorted(segments, key=lambda s: s.base)
    for a, b in zip(ordered, ordered[1:]):
        if a.base + a.limit > b.base:
            raise ValidationError(f"Segments {a.seg_id} and {b.seg_id} overlap in physical memory "
                                  f"([{a.base}, {a.base + a.limit}) and [{b.base}, {b.base + b.limit})).")


def translate(segments: List[Segment], seg_id: int, offset: int) -> SegTranslation:
    validate_table(segments)
    seg = next((s for s in segments if s.seg_id == seg_id), None)
    if seg is None:
        return SegTranslation(False, f"Invalid segment: segment {seg_id} does not exist (trap).", None, offset)
    if offset < 0:
        return SegTranslation(False, "Invalid offset: offsets cannot be negative (trap).", seg, offset)
    if offset >= seg.limit:
        return SegTranslation(False, f"Out of range: offset {offset} >= limit {seg.limit}. Addressing error (trap).",
                              seg, offset)
    return SegTranslation(True, "Offset is within bounds", seg, offset, seg.base + offset)


def gaps(segments: List[Segment], memory_end: Optional[int] = None):
    """Unallocated physical ranges between segments, as (start, end) pairs."""
    out, cursor = [], 0
    for s in sorted(segments, key=lambda s: s.base):
        if s.base > cursor:
            out.append((cursor, s.base))
        cursor = max(cursor, s.base + s.limit)
    if memory_end is not None and memory_end > cursor:
        out.append((cursor, memory_end))
    return out
