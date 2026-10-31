import json
from pathlib import Path
from typing import Final

import settings
from core.achievements import Achievement

PROGRESS_FILE: Final[Path] = settings.BASE_DIR / "data" / "progress.json"


class ProgressTracker:
    """Persists which achievements the player has unlocked, across app restarts.

    Mirrors GameRegistry's classmethod-based singleton pattern: state lives
    on the class itself rather than an instance, since there is exactly one
    player progress file per installation.
    """

    _unlocked: set[str] = set()
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
    def _ensure_loaded(cls) -> None:
        if cls._loaded:
            return
        cls._loaded = True
        if not PROGRESS_FILE.exists():
            return
        try:
            data = json.loads(PROGRESS_FILE.read_text(encoding="utf-8"))
            cls._unlocked = set(data.get("unlocked_achievements", []))
        except (json.JSONDecodeError, OSError):
            cls._unlocked = set()

    @classmethod
    def _save(cls) -> None:
        PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
        payload = {"unlocked_achievements": sorted(cls._unlocked)}
        PROGRESS_FILE.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
