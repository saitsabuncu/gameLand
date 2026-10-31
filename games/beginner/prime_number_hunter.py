from typing import Final

from PyQt6.QtWidgets import QGridLayout, QLabel, QPushButton, QVBoxLayout

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from utils.math_utils import sieve_of_eratosthenes

RANGE_MIN: Final[int] = 1
RANGE_MAX: Final[int] = 100
GRID_COLUMNS: Final[int] = 10

FOUND_COLOR: Final[str] = "background-color: #4caf50; color: white;"
MISTAKE_COLOR: Final[str] = "background-color: #f44336; color: white;"

# Mistake-count performance tiers for the completion summary, checked
# from strictest to loosest.
EXCELLENT_MAX_MISTAKES: Final[int] = 0
GREAT_MAX_MISTAKES: Final[int] = 5
GOOD_MAX_MISTAKES: Final[int] = 10


@register_game(display_name="Asal Sayı Avcısı", difficulty=Difficulty.BEGINNER)
class PrimeNumberHunterGame(BaseGame):
    """Click every prime number in a 1-100 grid; wrong clicks are tracked, not fatal."""

    def __init__(self) -> None:
        super().__init__()
        self._primes: set[int] = sieve_of_eratosthenes(RANGE_MAX)
        self._found_count: int = 0
        self._mistake_count: int = 0
        self._buttons: dict[int, QPushButton] = {}

        self._instructions_label = QLabel(
            f"{RANGE_MIN}-{RANGE_MAX} arasındaki tüm asal sayıları bul!"
        )
        self._progress_label = QLabel()
        self._summary_label = QLabel()

        self._grid_layout = QGridLayout()
        self._grid_layout.setSpacing(4)
        self._build_grid()

        layout = QVBoxLayout(self)
        layout.addWidget(self._instructions_label)
        layout.addWidget(self._progress_label)
        layout.addLayout(self._grid_layout)
        layout.addWidget(self._summary_label)
        layout.addStretch(1)

    def _build_grid(self) -> None:
        for number in range(RANGE_MIN, RANGE_MAX + 1):
            button = QPushButton(str(number))
            button.setFixedSize(50, 40)
            button.clicked.connect(lambda _checked, n=number: self._handle_number_clicked(n))
            row, column = divmod(number - RANGE_MIN, GRID_COLUMNS)
            self._grid_layout.addWidget(button, row, column)
            self._buttons[number] = button

    def start(self) -> None:
        self._found_count = 0
        self._mistake_count = 0
        self._summary_label.clear()
        for button in self._buttons.values():
            button.setEnabled(True)
            button.setStyleSheet("")
        self._update_progress_label()

    def reset(self) -> None:
        self.start()

    def _handle_number_clicked(self, number: int) -> None:
        button = self._buttons[number]
        button.setEnabled(False)

        if number in self._primes:
            button.setStyleSheet(FOUND_COLOR)
            self._found_count += 1
        else:
            button.setStyleSheet(MISTAKE_COLOR)
            self._mistake_count += 1

        self._update_progress_label()

        if self._found_count == len(self._primes):
            self._show_completion_summary()

    def _update_progress_label(self) -> None:
        self._progress_label.setText(
            f"Bulunan asal: {self._found_count}/{len(self._primes)} "
            f"| Yanlış tıklama: {self._mistake_count}"
        )

    def _show_completion_summary(self) -> None:
        performance_note = self._build_performance_note()
        self._summary_label.setText(
            f"Tüm asal sayıları buldun! 🎉 ({self._mistake_count} yanlış tıklama) — {performance_note}"
        )

    def _build_performance_note(self) -> str:
        if self._mistake_count <= EXCELLENT_MAX_MISTAKES:
            return "Mükemmel! 🏆"
        if self._mistake_count <= GREAT_MAX_MISTAKES:
            return "Harika iş! 🌟"
        if self._mistake_count <= GOOD_MAX_MISTAKES:
            return "İyi, ama daha dikkatli olabilirsin. 👍"
        return "Daha çok pratik yapmalısın. 💪"
