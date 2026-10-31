from typing import Final

from PyQt6.QtCore import Qt

RESTART_KEY: Final[Qt.Key] = Qt.Key.Key_R
PAUSE_KEY: Final[Qt.Key] = Qt.Key.Key_P

GLOBAL_SHORTCUT_KEYS: Final[frozenset[Qt.Key]] = frozenset({RESTART_KEY, PAUSE_KEY})
