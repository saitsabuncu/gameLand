import math
import random
from typing import Final

from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from core.achievements import Achievement
from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from core.progress_tracker import ProgressTracker
from ui.shortcut_aware_line_edit import ShortcutAwareLineEdit

MIN_NUMBER: Final[int] = 1
MAX_NUMBER: Final[int] = 100
OPTIMAL_ATTEMPTS: Final[int] = math.ceil(math.log2(MAX_NUMBER - MIN_NUMBER + 1))
GOOD_ATTEMPTS_MARGIN: Final[int] = 3


@register_game(display_name="Number Guessing", difficulty=Difficulty.BEGINNER)
class NumberGuessingGame(BaseGame):
    """Classic number guessing game with higher/lower hints."""

    def __init__(self) -> None:
        super().__init__()
        self._target_number: int = MIN_NUMBER
        self._attempt_count: int = 0

        self._instructions_label = QLabel(
            f"{MIN_NUMBER} ile {MAX_NUMBER} arasında bir sayı tuttum, bulabilir misin?"
        )
        self._feedback_label = QLabel()
        self._attempts_label = QLabel()

        self._guess_input = ShortcutAwareLineEdit()
        self._guess_input.setPlaceholderText(f"{MIN_NUMBER}-{MAX_NUMBER} arası bir sayı")
        self._guess_input.returnPressed.connect(self._handle_guess)

        self._submit_button = QPushButton("Tahmin Et")
        self._submit_button.clicked.connect(self._handle_guess)

        layout = QVBoxLayout(self)
        layout.addWidget(self._instructions_label)
        layout.addWidget(self._guess_input)
        layout.addWidget(self._submit_button)
        layout.addWidget(self._feedback_label)
        layout.addWidget(self._attempts_label)
        layout.addStretch(1)

    def start(self) -> None:
        self._target_number = random.randint(MIN_NUMBER, MAX_NUMBER)
        self._attempt_count = 0
        self._feedback_label.clear()
        self._update_attempts_label()
        self._guess_input.clear()
        self._guess_input.setEnabled(True)
        self._submit_button.setEnabled(True)
        self._guess_input.setFocus()

    def reset(self) -> None:
        self.start()

    def _handle_guess(self) -> None:
        guess_value = self._parse_guess(self._guess_input.text().strip())
        if guess_value is None:
            self._feedback_label.setText(
                f"Lütfen {MIN_NUMBER}-{MAX_NUMBER} arasında geçerli bir sayı girin."
            )
            return

        self._attempt_count += 1
        self._update_attempts_label()
        self._evaluate_guess(guess_value)
        self._guess_input.clear()

    def _parse_guess(self, text: str) -> int | None:
        try:
            value = int(text)
        except ValueError:
            return None
        if not (MIN_NUMBER <= value <= MAX_NUMBER):
            return None
        return value

    def _evaluate_guess(self, guess_value: int) -> None:
        if guess_value < self._target_number:
            self._feedback_label.setText("Daha yüksek bir sayı dene. ⬆️")
        elif guess_value > self._target_number:
            self._feedback_label.setText("Daha düşük bir sayı dene. ⬇️")
        else:
            self._handle_correct_guess()

    def _handle_correct_guess(self) -> None:
        performance_note = self._build_performance_note()
        self._feedback_label.setText(
            f"Doğru bildin! 🎉 Sayı {self._target_number} idi. "
            f"({self._attempt_count} denemede) — {performance_note}"
        )
        self._guess_input.setEnabled(False)
        self._submit_button.setEnabled(False)

        if self._attempt_count <= OPTIMAL_ATTEMPTS + GOOD_ATTEMPTS_MARGIN:
            ProgressTracker.unlock_achievement(Achievement.NUMBER_GUESSING_GOOD_OR_BETTER)

    def _build_performance_note(self) -> str:
        if self._attempt_count <= OPTIMAL_ATTEMPTS:
            return "Mükemmel! 🏆"
        if self._attempt_count <= OPTIMAL_ATTEMPTS + GOOD_ATTEMPTS_MARGIN:
            return "İyi iş! 👍"
        return f"Buldun ama daha hızlı olabilirdi (optimal: {OPTIMAL_ATTEMPTS} deneme). 🐢"

    def _update_attempts_label(self) -> None:
        self._attempts_label.setText(f"Deneme sayısı: {self._attempt_count}")
