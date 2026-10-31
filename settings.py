import os
import sys
from pathlib import Path

APP_NAME: str = "gameLand"
APP_VERSION: str = "0.1.0"

BASE_DIR: Path = Path(__file__).resolve().parent

WINDOW_WIDTH: int = 1024
WINDOW_HEIGHT: int = 720

DEFAULT_THEME: str = "light"


def _resolve_user_data_dir() -> Path:
    """Where per-user, writable app state (progress.json, …) lives.

    Deliberately NOT BASE_DIR: a PyInstaller onefile build runs from a
    temporary extraction folder (sys._MEIPASS) that's deleted when the
    process exits, so anything written next to "the app" would silently
    vanish between runs -- achievements would never actually persist once
    packaged. A real per-user app-data location is used instead, for both
    plain `python main.py` runs and frozen builds alike.
    """
    if sys.platform == "win32":
        root = Path(os.environ.get("APPDATA", Path.home() / "AppData" / "Roaming"))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local" / "share"))
    return root / APP_NAME


USER_DATA_DIR: Path = _resolve_user_data_dir()
