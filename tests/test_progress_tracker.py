from pathlib import Path

import pytest

import core.progress_tracker as progress_tracker_module
from core.achievements import Achievement
from core.base_game import GameLevel
from core.progress_tracker import ProgressTracker


@pytest.fixture(autouse=True)
def isolated_progress_tracker(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Points PROGRESS_FILE at a throwaway path and resets the tracker's
    in-memory class state before and after every test.

    ProgressTracker is a class-level singleton (state lives on the class,
    not an instance), so without this it would both leak state between
    tests and read/write the developer's real progress.json.
    """
    monkeypatch.setattr(progress_tracker_module, "PROGRESS_FILE", tmp_path / "progress.json")
    ProgressTracker._unlocked = set()
    ProgressTracker._levels = {}
    ProgressTracker._loaded = False
    yield
    ProgressTracker._unlocked = set()
    ProgressTracker._levels = {}
    ProgressTracker._loaded = False


def test_achievement_starts_locked() -> None:
    assert ProgressTracker.has_achievement(Achievement.NUMBER_GUESSING_GOOD_OR_BETTER) is False


def test_unlock_achievement_persists_to_disk() -> None:
    ProgressTracker.unlock_achievement(Achievement.MATH_QUIZ_GOOD_OR_BETTER)
    assert ProgressTracker.has_achievement(Achievement.MATH_QUIZ_GOOD_OR_BETTER) is True
    assert progress_tracker_module.PROGRESS_FILE.exists()


def test_unlocked_achievement_survives_a_fresh_load() -> None:
    ProgressTracker.unlock_achievement(Achievement.PRIME_HUNTER_GOOD_OR_BETTER)

    # Simulate a fresh app start: forget in-memory state, force a reload
    # from disk on the next query.
    ProgressTracker._loaded = False
    ProgressTracker._unlocked = set()

    assert ProgressTracker.has_achievement(Achievement.PRIME_HUNTER_GOOD_OR_BETTER) is True


def test_unlocking_twice_is_a_harmless_no_op() -> None:
    ProgressTracker.unlock_achievement(Achievement.MATH_QUIZ_GOOD_OR_BETTER)
    first_write_time = progress_tracker_module.PROGRESS_FILE.stat().st_mtime_ns

    ProgressTracker.unlock_achievement(Achievement.MATH_QUIZ_GOOD_OR_BETTER)
    second_write_time = progress_tracker_module.PROGRESS_FILE.stat().st_mtime_ns

    assert first_write_time == second_write_time  # no second write happened


def test_corrupted_progress_file_is_treated_as_empty(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    broken_file = tmp_path / "broken.json"
    broken_file.write_text("not valid json", encoding="utf-8")
    monkeypatch.setattr(progress_tracker_module, "PROGRESS_FILE", broken_file)
    ProgressTracker._unlocked = set()
    ProgressTracker._loaded = False

    assert ProgressTracker.has_achievement(Achievement.NUMBER_GUESSING_GOOD_OR_BETTER) is False


def test_get_level_returns_default_when_nothing_saved() -> None:
    assert ProgressTracker.get_level("sudoku", default=GameLevel.MEDIUM) is GameLevel.MEDIUM


def test_set_level_then_get_level_round_trips() -> None:
    ProgressTracker.set_level("sudoku", GameLevel.HARD)
    assert ProgressTracker.get_level("sudoku", default=GameLevel.MEDIUM) is GameLevel.HARD


def test_level_is_saved_independently_per_game() -> None:
    ProgressTracker.set_level("sudoku", GameLevel.HARD)
    ProgressTracker.set_level("math_quiz", GameLevel.EASY)
    assert ProgressTracker.get_level("sudoku", default=GameLevel.MEDIUM) is GameLevel.HARD
    assert ProgressTracker.get_level("math_quiz", default=GameLevel.MEDIUM) is GameLevel.EASY


def test_level_survives_a_fresh_load() -> None:
    ProgressTracker.set_level("sudoku", GameLevel.EASY)
    ProgressTracker._loaded = False
    ProgressTracker._levels = {}

    assert ProgressTracker.get_level("sudoku", default=GameLevel.MEDIUM) is GameLevel.EASY


def test_get_level_falls_back_to_default_on_unrecognized_stored_value(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # Simulates a progress.json written by a future version with a GameLevel
    # option that doesn't exist in this build -- must not crash.
    ProgressTracker._loaded = True
    ProgressTracker._levels = {"sudoku": "Cok Zor"}

    assert ProgressTracker.get_level("sudoku", default=GameLevel.MEDIUM) is GameLevel.MEDIUM
