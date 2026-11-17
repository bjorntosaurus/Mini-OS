"""User preferences (Settings screen) persisted with QSettings."""
from PySide6.QtCore import QObject, QSettings, Signal

DEFAULTS = {"mode": "light", "accent": 0, "sounds": True, "motion": False, "speed": 1, "tips": True, "skin": "xp", "wallpaper": "builtin:meadow", "wp_mode": "Fill", "wp_library": ""}
ACCENTS = ["#c4f06a", "#ffa3c4", "#c5b3f2", "#ffcc62", "#84d9e0"]
SPEEDS = [0.5, 1.0, 2.0, 4.0]


class Prefs(QObject):
    changed = Signal()

    def __init__(self):
        super().__init__()
        self._s = QSettings("Kernel98", "OSSimulator")
        self.values = dict(DEFAULTS)
        for k, d in DEFAULTS.items():
            v = self._s.value(k, d)
            if isinstance(d, bool):
                v = str(v).lower() in ("true", "1")
            elif isinstance(d, str):
                v = str(v)
            elif isinstance(d, int):
                v = int(v)
            self.values[k] = v

    def __getitem__(self, k):
        return self.values[k]

    def update(self, **kw):
        self.values.update(kw)
        self.changed.emit()

    def save(self):
        for k, v in self.values.items():
            self._s.setValue(k, v)
        self._s.sync()

    def restore(self):
        self.values = dict(DEFAULTS)
        self.changed.emit()

    @property
    def accent_override(self):
        return None if self["accent"] == 0 else ACCENTS[self["accent"]]

    @property
    def speed(self):
        return SPEEDS[self["speed"]]


_PREFS = None


def get_prefs():
    """Single shared Prefs instance (both desktop skins use it)."""
    global _PREFS
    if _PREFS is None:
        _PREFS = Prefs()
    return _PREFS
