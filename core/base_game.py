from abc import ABCMeta, abstractmethod
from enum import Enum

from PyQt6.QtWidgets import QWidget


class Difficulty(Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class _QWidgetABCMeta(type(QWidget), ABCMeta):
    """Merges PyQt6's sip metaclass with ABCMeta so BaseGame can use @abstractmethod."""


class BaseGame(QWidget, metaclass=_QWidgetABCMeta):
    """Contract that every game widget must implement."""

    display_name: str
    difficulty: Difficulty

    @abstractmethod
    def start(self) -> None:
        """Resets internal state and renders the initial view."""
        ...

    @abstractmethod
    def reset(self) -> None:
        """Restarts the current game session."""
        ...

    def toggle_pause(self) -> None:
        """Pauses or resumes the game, bound to the P key by GameContainer.

        Optional: most games (turn-based, no timer) have no notion of pause
        and can safely leave this as a no-op. Timer-driven games (e.g. Math
        Countdown) should override it.
        """
