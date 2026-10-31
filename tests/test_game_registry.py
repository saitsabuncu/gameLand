import games  # noqa: F401  -- import alone registers every game, see games/__init__.py
from core.base_game import Difficulty
from core.game_registry import GameRegistry

EXPECTED_GAME_COUNT: int = 10
EXPECTED_COUNT_BY_DIFFICULTY: dict[Difficulty, int] = {
    Difficulty.BEGINNER: 4,
    Difficulty.INTERMEDIATE: 3,
    Difficulty.ADVANCED: 3,
}


def test_all_games_are_discovered() -> None:
    assert len(GameRegistry.get_all()) == EXPECTED_GAME_COUNT


def test_games_are_distributed_across_difficulties_as_expected() -> None:
    for difficulty, expected_count in EXPECTED_COUNT_BY_DIFFICULTY.items():
        assert len(GameRegistry.get_by_difficulty(difficulty)) == expected_count


def test_every_game_has_a_unique_display_name() -> None:
    display_names = [entry.display_name for entry in GameRegistry.get_all()]
    assert len(display_names) == len(set(display_names))


def test_every_game_declares_non_empty_instructions() -> None:
    for entry in GameRegistry.get_all():
        assert entry.game_class.instructions.strip() != "", entry.display_name
