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
        layout = QGridLayout(page)

        if not entries:
            layout.addWidget(QLabel("No games registered yet."), 0, 0)
            return page

        for index, entry in enumerate(entries):
            row, column = divmod(index, GAMES_PER_ROW)
            layout.addWidget(self._build_game_button(entry), row, column)

        return page

    def _build_game_button(self, entry: GameEntry) -> QPushButton:
        label = f"🔒 {entry.display_name}" if entry.is_locked else entry.display_name
        button = QPushButton(label)
        button.setMinimumHeight(80)
        if entry.is_locked:
            button.setStyleSheet("color: gray;")
            button.setToolTip(entry.unlock_description)
        button.clicked.connect(lambda: self._launch_game(entry))
        return button

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
