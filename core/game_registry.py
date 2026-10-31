from dataclasses import dataclass, field
from typing import Type

from core.achievements import Achievement
from core.base_game import BaseGame, Difficulty
from core.progress_tracker import ProgressTracker


@dataclass(frozen=True)
class GameEntry:
    game_class: Type[BaseGame]
    display_name: str
    difficulty: Difficulty
    required_achievements: frozenset[Achievement] = field(default_factory=frozenset)
    unlock_description: str = ""

    @property
    def is_locked(self) -> bool:
        """A game with no requirements is always unlocked; otherwise holding
        ANY one of its required achievements is enough to unlock it."""
        if not self.required_achievements:
            return False
        return not any(
            ProgressTracker.has_achievement(achievement)
            for achievement in self.required_achievements
        )


class GameRegistry:
    """Central registry populated via the @register_game decorator."""

    _entries: list[GameEntry] = []

    @classmethod
    def register(
        cls,
        game_class: Type[BaseGame],
        display_name: str,
        difficulty: Difficulty,
        required_achievements: frozenset[Achievement] = frozenset(),
        unlock_description: str = "",
    ) -> None:
        cls._entries.append(
            GameEntry(
                game_class,
                display_name,
                difficulty,
                required_achievements,
                unlock_description,
            )
        )

    @classmethod
    def get_all(cls) -> list[GameEntry]:
        return list(cls._entries)

    @classmethod
    def get_by_difficulty(cls, difficulty: Difficulty) -> list[GameEntry]:
        return [entry for entry in cls._entries if entry.difficulty == difficulty]


def register_game(
    display_name: str,
    difficulty: Difficulty,
    required_achievements: frozenset[Achievement] = frozenset(),
    unlock_description: str = "",
):
    """Class decorator that auto-registers a BaseGame subclass.

    required_achievements/unlock_description: optional gating. If omitted,
    the game is always unlocked (current behavior for every existing game).
    """

    def decorator(game_class: Type[BaseGame]) -> Type[BaseGame]:
        game_class.display_name = display_name
        game_class.difficulty = difficulty
        GameRegistry.register(
            game_class, display_name, difficulty, required_achievements, unlock_description
        )
        return game_class

    return decorator
