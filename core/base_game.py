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
