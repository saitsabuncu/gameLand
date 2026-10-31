from abc import ABCMeta, abstractmethod
from enum import Enum

from PyQt6.QtWidgets import QWidget


class Difficulty(Enum):
    BEGINNER = "Başlangıç"
    INTERMEDIATE = "Orta"
    ADVANCED = "İleri"


class GameLevel(Enum):
    """An individual game's internal Easy/Medium/Hard setting.

    Deliberately a separate enum from Difficulty, not three more values on
    it: Difficulty picks which main-menu TAB a game lives under (fixed per
    game, set once via @register_game); GameLevel is a setting the player
    changes freely INSIDE a game that supports it (e.g. Sudoku's clue
    count), independent of which tab it's in. Conflating the two would mean
    changing a game's in-game level could also move it to a different menu
    tab, which makes no sense.

    Optional, like toggle_pause(): a game opts in by reading/writing it
    itself (see games/advanced/sudoku.py) rather than BaseGame requiring it,
    since plenty of games (Monty Hall, Chaos Game, ...) have no meaningful
    difficulty axis at all.
    """

    EASY = "Kolay"
    MEDIUM = "Orta"
    HARD = "Zor"


class _QWidgetABCMeta(type(QWidget), ABCMeta):
    """Merges PyQt6's sip metaclass with ABCMeta so BaseGame can use @abstractmethod."""


class BaseGame(QWidget, metaclass=_QWidgetABCMeta):
    """Contract that every game widget must implement."""

    display_name: str
    difficulty: Difficulty
    instructions: str = ""

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
