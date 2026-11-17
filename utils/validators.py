"""Input validation helpers shared by every module. All raise ValidationError with a
human-readable message that the GUI shows in a dialog / status bar."""
import re


class ValidationError(ValueError):
    """Raised for any invalid user input."""


def parse_int(text, field, minimum=None, maximum=None):
    s = str(text).strip().replace(",", "") if not isinstance(text, int) else str(text)
    if s == "":
        raise ValidationError(f"{field}: value is empty.")
    if not re.fullmatch(r"[+-]?\d+", s):
        raise ValidationError(f"{field}: '{text}' is not a whole number.")
    v = int(s)
    if minimum is not None and v < minimum:
        raise ValidationError(f"{field}: {v} is below the minimum of {minimum}.")
    if maximum is not None and v > maximum:
        raise ValidationError(f"{field}: {v} is above the maximum of {maximum}.")
    return v


def parse_float(text, field, minimum=None, maximum=None):
    s = str(text).strip()
    if s == "":
        raise ValidationError(f"{field}: value is empty.")
    try:
        v = float(s)
    except ValueError:
        raise ValidationError(f"{field}: '{text}' is not a number.") from None
    if minimum is not None and v < minimum:
        raise ValidationError(f"{field}: {v} is below the minimum of {minimum}.")
    if maximum is not None and v > maximum:
        raise ValidationError(f"{field}: {v} is above the maximum of {maximum}.")
    return v


def parse_int_list(text, field, minimum=None, maximum=None, allow_empty=False):
    """Parse '1, 2 3;4' into [1,2,3,4]."""
    parts = [p for p in re.split(r"[,\s;]+", str(text).strip()) if p != ""]
    if not parts:
        if allow_empty:
            return []
        raise ValidationError(f"{field}: the list is empty.")
    return [parse_int(p, f"{field} item {i + 1}", minimum, maximum) for i, p in enumerate(parts)]


def check_matrix(m, rows, cols, name):
    if len(m) != rows:
        raise ValidationError(f"{name}: expected {rows} rows, got {len(m)}.")
    for i, r in enumerate(m):
        if len(r) != cols:
            raise ValidationError(f"{name}: row {i} has {len(r)} values, expected {cols}.")
        for v in r:
            if not isinstance(v, int) or isinstance(v, bool):
                raise ValidationError(f"{name}: row {i} contains a non-integer value.")
            if v < 0:
                raise ValidationError(f"{name}: row {i} contains a negative value ({v}).")
