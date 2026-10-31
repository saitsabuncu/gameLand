from typing import cast

from PyQt6.QtCore import QEvent, Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QLineEdit

from ui.game_shortcuts import GLOBAL_SHORTCUT_KEYS


class ShortcutAwareLineEdit(QLineEdit):
    """QLineEdit that yields global game shortcuts (R, P) to GameContainer.

    By default QLineEdit claims every plain key press as text input via the
    ShortcutOverride event, which silently swallows single-letter
    ApplicationShortcut key presses (e.g. R for restart) while this widget
    has focus. This subclass explicitly releases only the reserved global
    shortcut keys so GameContainer's shortcuts still fire during typing,
    while every other key continues to behave as normal text input.
    """

    def event(self, e: QEvent) -> bool:
        if e.type() == QEvent.Type.ShortcutOverride:
            key_event = cast(QKeyEvent, e)
            if (
                key_event.key() in GLOBAL_SHORTCUT_KEYS
                and key_event.modifiers() == Qt.KeyboardModifier.NoModifier
            ):
                e.ignore()
                return True
        return super().event(e)
