"""Paging: logical -> physical address translation with a page table."""
from typing import List, Optional, Tuple

from models.records import Translation
from utils.validators import ValidationError

PageEntry = Tuple[Optional[int], bool]      # (frame, valid)


def validate_config(page_size: int, num_frames: int, table: List[PageEntry]):
    if page_size < 1:
        raise ValidationError("Page size must be at least 1 byte.")
    if num_frames < 1:
        raise ValidationError("The machine needs at least 1 physical frame.")
    if not table:
        raise ValidationError("The page table is empty. Add at least one page.")
    used = {}
    for page, (frame, valid) in enumerate(table):
        if not valid:
            continue
        if frame is None:
            raise ValidationError(f"Page {page} is marked valid but has no frame.")
        if frame < 0 or frame >= num_frames:
            raise ValidationError(f"Page {page} maps to frame {frame}, but only frames 0..{num_frames - 1} exist.")
        if frame in used:
            raise ValidationError(f"Pages {used[frame]} and {page} both map to frame {frame}.")
        used[frame] = page


def frame_map(table: List[PageEntry], num_frames: int) -> List[Optional[int]]:
    frames = [None] * num_frames
    for page, (frame, valid) in enumerate(table):
        if valid and frame is not None and 0 <= frame < num_frames:
            frames[frame] = page
    return frames


def translate(logical: int, page_size: int, table: List[PageEntry], num_frames: int) -> Translation:
    validate_config(page_size, num_frames, table)
    if logical < 0:
        raise ValidationError("A logical address cannot be negative.")
    page, offset = divmod(logical, page_size)
    if page >= len(table):
        return Translation("invalid", f"Invalid address: page {page} is outside the logical address space "
                           f"({len(table)} pages x {page_size} bytes = {len(table) * page_size} bytes).",
                           page, offset)
    frame, valid = table[page]
    if not valid:
        return Translation("page_fault", f"Page {page} is not resident. Accessing it triggers a page fault.",
                           page, offset)
    return Translation("ok", "Address resolved.", page, offset, frame, frame * page_size + offset)
