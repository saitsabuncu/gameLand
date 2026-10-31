import json
from pathlib import Path
from typing import Final

import settings
from core.achievements import Achievement
from core.base_game import GameLevel

PROGRESS_FILE: Final[Path] = settings.USER_DATA_DIR / "progress.json"


class ProgressTracker:
    """Persists which achievements the player has unlocked and each game's
    last-chosen GameLevel, across app restarts.

    Mirrors GameRegistry's classmethod-based singleton pattern: state lives
    on the class itself rather than an instance, since there is exactly one
    player progress file per installation.
    """

    _unlocked: set[str] = set()
    _levels: dict[str, str] = {}
    _loaded: bool = False

    @classmethod
    def has_achievement(cls, achievement: Achievement) -> bool:
        cls._ensure_loaded()
        return achievement.value in cls._unlocked

    @classmethod
    def unlock_achievement(cls, achievement: Achievement) -> None:
        cls._ensure_loaded()
        if achievement.value in cls._unlocked:
            return
        cls._unlocked.add(achievement.value)
        cls._save()

    @classmethod
    def get_level(cls, game_key: str, default: GameLevel) -> GameLevel:
        """Returns the player's last-saved GameLevel for `game_key`, or
        `default` if nothing was ever saved (or the saved value is stale --
        e.g. from a GameLevel option that no longer exists)."""
        cls._ensure_loaded()
        stored_value = cls._levels.get(game_key)
        if stored_value is None:
            return default
        try:
            return GameLevel(stored_value)
        except ValueError:
            return default

    @classmethod
    def set_level(cls, game_key: str, level: GameLevel) -> None:
        cls._ensure_loaded()
        if cls._levels.get(game_key) == level.value:
            return
        cls._levels[game_key] = level.value
        cls._save()

    @classmethod
    def _ensure_loaded(cls) -> None:
        if cls._loaded:
            return
        cls._loaded = True
        if not PROGRESS_FILE.exists():
            return
        try:
            data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            cls._unlocked = set(data.get("unlocked_achievements", []))
            cls._levels = dict(data.get("game_levels", {}))
        except (json.JSONDecodeError, OSError):
            cls._unlocked = set()
            cls._levels = {}

    @classmethod
    def _save(cls) -> None:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "unlocked_achievements": sorted(cls._unlocked),
            "game_levels": cls._levels,
        }
        PROGRESS_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
