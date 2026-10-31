from pathlib import Path

import pytest

import core.progress_tracker as progress_tracker_module
from core.achievements import Achievement
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
    ProgressTracker._loaded = False
    yield
    ProgressTracker._unlocked = set()
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
