from typing import Final

from PyQt6.QtWidgets import (
    QGridLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QStackedWidget,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

import settings
from core.base_game import Difficulty
from core.game_registry import GameEntry, GameRegistry
from ui.game_container import GameContainer

GAMES_PER_ROW: int = 3
CARD_MIN_HEIGHT_PX: Final[int] = 110
CARD_SPACING_PX: Final[int] = 16
PAGE_MARGIN_PX: Final[int] = 24

_LOCKED_ACCENT_COLOR: Final[str] = "#9e9e9e"
_LOCKED_TEXT_COLOR: Final[str] = "#8a8a8a"

# One accent color per difficulty, used as each card's left border -- a
# quick visual cue for which tier a game belongs to even before reading
# its name (green=easier, red=harder is a common, low-effort convention).
_DIFFICULTY_ACCENT_COLORS: Final[dict[Difficulty, str]] = {
    Difficulty.BEGINNER: "#43a047",
    Difficulty.INTERMEDIATE: "#fb8c00",
    Difficulty.ADVANCED: "#8e24aa",
}

# Keyed by display_name rather than a field on GameEntry/BaseGame -- purely
# a menu-presentation concern, so it stays local to this file instead of
# growing the registry/decorator contract every other game module uses.
_GAME_ICONS: Final[dict[str, str]] = {
    "Number Guessing": "🎯",
    "Math Quiz Challenge": "➗",
    "Asal Sayı Avcısı": "🔍",
    "Hangman": "🔤",
    "Nim Game": "🪨",
    "Monty Hall Problemi Simülasyonu": "🚪",
    "Math Countdown": "⏱️",
    "2048": "🧮",
    "Sudoku": "🔢",
    "Kaos Oyunu": "🌀",
}
_DEFAULT_GAME_ICON: Final[str] = "🎮"


class MainWindow(QMainWindow):
    """Top-level window: a difficulty-tabbed game menu plus a game container."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle(settings.APP_NAME)
        self.resize(settings.WINDOW_WIDTH, settings.WINDOW_HEIGHT)

        self._stack = QStackedWidget()
        self._game_container = GameContainer(on_back=self._show_menu)

        self._stack.addWidget(self._build_menu())
        self._stack.addWidget(self._game_container)

        self.setCentralWidget(self._stack)

    def _build_menu(self) -> QWidget:
        tabs = QTabWidget()
        for difficulty in Difficulty:
            tabs.addTab(self._build_difficulty_page(difficulty), difficulty.value)
        return tabs

    def _build_difficulty_page(self, difficulty: Difficulty) -> QWidget:
        entries = GameRegistry.get_by_difficulty(difficulty)

        page = QWidget()
        page_layout = QVBoxLayout(page)
        page_layout.setContentsMargins(
            PAGE_MARGIN_PX, PAGE_MARGIN_PX, PAGE_MARGIN_PX, PAGE_MARGIN_PX
        )

        if not entries:
            page_layout.addWidget(QLabel("Henüz oyun eklenmedi."))
            page_layout.addStretch(1)
            return page

        card_grid = QGridLayout()
        card_grid.setSpacing(CARD_SPACING_PX)
        for index, entry in enumerate(entries):
            row, column = divmod(index, GAMES_PER_ROW)
            card_grid.addWidget(self._build_game_button(entry), row, column)

        page_layout.addLayout(card_grid)
        # Absorbs all leftover vertical space below the cards instead of
        # QGridLayout silently distributing it as extra gaps *between*
        # rows -- the same fix as the Sudoku board, applied to a plain
        # QGridLayout dropped straight into a full-window page.
        page_layout.addStretch(1)
        return page

    def _build_game_button(self, entry: GameEntry) -> QPushButton:
        icon = _GAME_ICONS.get(entry.display_name, _DEFAULT_GAME_ICON)
        button_text = f"{icon}\n{entry.display_name}"
        if entry.is_locked:
            button_text += "\n🔒 Kilitli"

        button = QPushButton(button_text)
        button.setMinimumHeight(CARD_MIN_HEIGHT_PX)
        button.setStyleSheet(self._card_stylesheet(entry))
        if entry.is_locked:
            button.setToolTip(entry.unlock_description)
        button.clicked.connect(lambda: self._launch_game(entry))
        return button

    def _card_stylesheet(self, entry: GameEntry) -> str:
        if entry.is_locked:
            accent_color, text_color = _LOCKED_ACCENT_COLOR, _LOCKED_TEXT_COLOR
        else:
            accent_color, text_color = _DIFFICULTY_ACCENT_COLORS[entry.difficulty], "#1a1a1a"

        return (
            "QPushButton {"
            "background-color: #ffffff; border: 1px solid #e0e0e0; "
            f"border-left: 5px solid {accent_color}; border-radius: 8px; "
            f"padding: 10px; font-size: 15px; font-weight: 600; color: {text_color};"
            "}"
            "QPushButton:hover { background-color: #f7f7f7; }"
        )

    def _launch_game(self, entry: GameEntry) -> None:
        if entry.is_locked:
            self._show_lock_message(entry)
            return
        game_instance = entry.game_class()
        self._game_container.load_game(game_instance)
        self._stack.setCurrentWidget(self._game_container)

    def _show_lock_message(self, entry: GameEntry) -> None:
        QMessageBox.information(self, "Kilitli Oyun", entry.unlock_description)

    def _show_menu(self) -> None:
        self._refresh_menu()
        self._stack.setCurrentIndex(0)

    def _refresh_menu(self) -> None:
        # Rebuilt on every return to the menu so a newly-unlocked game's
        # lock state (e.g. Hangman after a good Number Guessing round)
        # is reflected immediately, without restarting the app.
        old_menu = self._stack.widget(0)
        new_menu = self._build_menu()
        self._stack.removeWidget(old_menu)
        old_menu.deleteLater()
        self._stack.insertWidget(0, new_menu)
