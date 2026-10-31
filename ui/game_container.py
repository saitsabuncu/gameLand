from typing import Callable

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeySequence, QShortcut
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

from core.base_game import BaseGame


class GameContainer(QWidget):
    """Hosts a single active BaseGame instance with a header and a back action."""

    def __init__(self, on_back: Callable[[], None]) -> None:
        super().__init__()
        self._on_back = on_back
        self._current_game: BaseGame | None = None

        self._title_label = QLabel()
        self._title_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        back_button = QPushButton("← Menu")
        back_button.clicked.connect(self._handle_back)

        restart_button = QPushButton("Restart")
        restart_button.clicked.connect(self._handle_restart)

        header_layout = QHBoxLayout()
        header_layout.addWidget(back_button)
        header_layout.addWidget(self._title_label, stretch=1)
        header_layout.addWidget(restart_button)

        self._body_layout = QVBoxLayout()

        self._restart_shortcut = QShortcut(QKeySequence(Qt.Key.Key_R), self)
        self._restart_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._restart_shortcut.activated.connect(self._handle_restart)

        self._pause_shortcut = QShortcut(QKeySequence(Qt.Key.Key_P), self)
        self._pause_shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)
        self._pause_shortcut.activated.connect(self._handle_toggle_pause)

        root_layout = QVBoxLayout(self)
        root_layout.addLayout(header_layout)
        root_layout.addLayout(self._body_layout, stretch=1)

    def load_game(self, game: BaseGame) -> None:
        self._clear_body()
        self._current_game = game
        self._title_label.setText(game.display_name)
        self._body_layout.addWidget(game)
        game.start()

    def _handle_back(self) -> None:
        self._clear_body()
        self._on_back()

    def _handle_restart(self) -> None:
        if self._current_game is not None:
            self._current_game.reset()

    def _handle_toggle_pause(self) -> None:
        if self._current_game is not None:
            self._current_game.toggle_pause()

    def _clear_body(self) -> None:
        if self._current_game is not None:
            self._body_layout.removeWidget(self._current_game)
            self._current_game.deleteLater()
            self._current_game = None
