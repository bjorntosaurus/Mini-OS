"""Paging: logical -> physical address translation with a page table."""
from typing import List, Optional, Tuple

from models.records import Translation
from utils.validators import ValidationError

PageEntry = Tuple[Optional[int], bool]      # (frame, valid)


# Reject impossible machine / page-table configurations before translating anything.
def validate_config(page_size: int, num_frames: int, table: List[PageEntry]):
    """Raise ValidationError for page size < 1, frames < 1, an empty table, a valid entry without a frame,
    a frame outside 0..num_frames-1, or two pages mapped to the same frame.
    """
    if page_size < 1:
        raise ValidationError("Page size must be at least 1 byte.")
    if num_frames < 1:
        raise ValidationError("The machine needs at least 1 physical frame.")
    if not table:
        raise ValidationError("The page table is empty. Add at least one page.")
    # used maps frame -> page so two pages can't claim the same physical frame.
    used = {}
    # Only VALID entries need a real frame; invalid entries are 'not in memory' and their frame is ignored.
    for page, (frame, valid) in enumerate(table):
        # Page exists but is not resident in RAM -> page fault (the OS would load it from disk).
        if not valid:
            continue
        if frame is None:
            raise ValidationError(f"Page {page} is marked valid but has no frame.")
        if frame < 0 or frame >= num_frames:
            raise ValidationError(f"Page {page} maps to frame {frame}, but only frames 0..{num_frames - 1} exist.")
        if frame in used:
            raise ValidationError(f"Pages {used[frame]} and {page} both map to frame {frame}.")
        used[frame] = page


# Inverse of the page table: for each physical frame, which page (if any) lives in it.
def frame_map(table: List[PageEntry], num_frames: int) -> List[Optional[int]]:
    """Return a list with one item per physical frame: the page stored there, or None if the frame is free."""
    frames = [None] * num_frames
    for page, (frame, valid) in enumerate(table):
        if valid and frame is not None and 0 <= frame < num_frames:
            frames[frame] = page
    return frames


# Logical -> physical translation.
def translate(logical: int, page_size: int, table: List[PageEntry], num_frames: int) -> Translation:
    """Translate `logical` using the page table.

    Args:
        table: list indexed by page number of (frame, valid) pairs.
    Returns:
        Translation with status 'ok' (frame + physical set), 'page_fault' (page not resident) or 'invalid'
        (page number outside the table). Raises ValidationError for a negative address or a bad configuration.
    """
    validate_config(page_size, num_frames, table)
    if logical < 0:
        raise ValidationError("A logical address cannot be negative.")
    # Split the logical address:  page = address // page size,  offset = address % page size.
    page, offset = divmod(logical, page_size)
    # Address beyond the logical address space (more pages than the table has) -> invalid address, not a page fault.
    if page >= len(table):
        return Translation("invalid", f"Invalid address: page {page} is outside the logical address space "
                           f"({len(table)} pages x {page_size} bytes = {len(table) * page_size} bytes).",
                           page, offset)
    # Look the page up in the page table.
    frame, valid = table[page]
    if not valid:
        return Translation("page_fault", f"Page {page} is not resident. Accessing it triggers a page fault.",
                           page, offset)
    # Resident page: physical address = frame * page size + offset.
    return Translation("ok", "Address resolved.", page, offset, frame, frame * page_size + offset)
