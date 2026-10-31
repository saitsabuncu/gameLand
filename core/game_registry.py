from dataclasses import dataclass
from typing import Type

from core.base_game import BaseGame, Difficulty


@dataclass(frozen=True)
class GameEntry:
    game_class: Type[BaseGame]
    display_name: str
    difficulty: Difficulty


class GameRegistry:
    """Central registry populated via the @register_game decorator."""

    _entries: list[GameEntry] = []

    @classmethod
    def register(cls, game_class: Type[BaseGame], display_name: str, difficulty: Difficulty) -> None:
        cls._entries.append(GameEntry(game_class, display_name, difficulty))

    @classmethod
    def get_all(cls) -> list[GameEntry]:
        return list(cls._entries)

    @classmethod
    def get_by_difficulty(cls, difficulty: Difficulty) -> list[GameEntry]:
        return [entry for entry in cls._entries if entry.difficulty == difficulty]


def register_game(display_name: str, difficulty: Difficulty):
    """Class decorator that auto-registers a BaseGame subclass."""

    def decorator(game_class: Type[BaseGame]) -> Type[BaseGame]:
        game_class.display_name = display_name
        game_class.difficulty = difficulty
        GameRegistry.register(game_class, display_name, difficulty)
        return game_class

    return decorator
