from abc import ABC, abstractmethod
from enum import Enum

from PyQt6.QtWidgets import QWidget


class Difficulty(Enum):
    BEGINNER = "Beginner"
    INTERMEDIATE = "Intermediate"
    ADVANCED = "Advanced"


class BaseGame(ABC, QWidget):
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
