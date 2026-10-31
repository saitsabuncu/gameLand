import math
import random
from typing import Final

from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.achievements import Achievement
from core.base_game import BaseGame, Difficulty, GameLevel
from core.game_registry import register_game
from core.progress_tracker import ProgressTracker
from ui.shortcut_aware_line_edit import ShortcutAwareLineEdit

MIN_NUMBER: Final[int] = 1
GOOD_ATTEMPTS_MARGIN: Final[int] = 3

# Key under which the player's last-picked GameLevel is saved via
# ProgressTracker -- a stable internal id, independent of display_name.
_PROGRESS_KEY: Final[str] = "number_guessing"

# GameLevel widens the guessing range -- the only axis this game has.
# OPTIMAL_ATTEMPTS (binary-search bound) is derived from MAX_NUMBER, so a
# wider range at harder levels automatically earns a slightly more
# generous attempt budget too, with no extra bookkeeping needed.
_MAX_NUMBER_BY_LEVEL: Final[dict[GameLevel, int]] = {
    GameLevel.EASY: 50,
    GameLevel.MEDIUM: 100,
    GameLevel.HARD: 200,
}


def _optimal_attempts_for(max_number: int) -> int:
    return math.ceil(math.log2(max_number - MIN_NUMBER + 1))


@register_game(
    display_name="Number Guessing",
    difficulty=Difficulty.BEGINNER,
    instructions=(
        "Belirli bir aralıkta rastgele tutulan bir sayı var. Tahminini gir ve "
        "'daha yüksek/daha düşük' ipucuna göre yeni bir tahmin yap. Deneme hakkın "
        "sınırsız, ama ne kadar az denemede bulursan performans etiketin o kadar iyi olur "
        "(optimal, ikili arama mantığıyla hesaplanır).\n\n"
        "Üstteki menüden Kolay/Orta/Zor seviyesini seçebilirsin -- seviye, aralığın "
        "genişliğini belirler (Kolay 1-50, Orta 1-100, Zor 1-200). Seçtiğin seviye "
        "hatırlanır ve bir dahaki açılışta otomatik seçili gelir."
    ),
)
class NumberGuessingGame(BaseGame):
    """Classic number guessing game with higher/lower hints.

    GameLevel (Easy/Medium/Hard) widens MIN_NUMBER..max_number; the
    player's choice is loaded from and saved to ProgressTracker.
    """

    def __init__(self) -> None:
        super().__init__()
        self._level: GameLevel = ProgressTracker.get_level(_PROGRESS_KEY, default=GameLevel.MEDIUM)
        self._max_number: int = _MAX_NUMBER_BY_LEVEL[self._level]
        self._optimal_attempts: int = _optimal_attempts_for(self._max_number)
        self._target_number: int = MIN_NUMBER
        self._attempt_count: int = 0

        self._level_combo = QComboBox()
        for level in GameLevel:
            self._level_combo.addItem(level.value, userData=level)
        self._level_combo.setCurrentIndex(self._level_combo.findData(self._level))
        self._level_combo.currentIndexChanged.connect(self._handle_level_changed)

        level_layout = QHBoxLayout()
        level_layout.addWidget(QLabel("Seviye:"))
        level_layout.addWidget(self._level_combo)
        level_layout.addStretch(1)

        self._instructions_label = QLabel()
        self._feedback_label = QLabel()
        self._attempts_label = QLabel()

        self._guess_input = ShortcutAwareLineEdit()
        self._guess_input.returnPressed.connect(self._handle_guess)

        self._submit_button = QPushButton("Tahmin Et")
        self._submit_button.clicked.connect(self._handle_guess)

        layout = QVBoxLayout(self)
        layout.addLayout(level_layout)
        layout.addWidget(self._instructions_label)
        layout.addWidget(self._guess_input)
        layout.addWidget(self._submit_button)
        layout.addWidget(self._feedback_label)
        layout.addWidget(self._attempts_label)
        layout.addStretch(1)

    def start(self) -> None:
        self._target_number = random.randint(MIN_NUMBER, self._max_number)
        self._attempt_count = 0
        self._feedback_label.clear()
        self._update_attempts_label()
        self._update_range_dependent_labels()
        self._guess_input.clear()
        self._guess_input.setEnabled(True)
        self._submit_button.setEnabled(True)
        self._guess_input.setFocus()

    def reset(self) -> None:
        self.start()

    def _handle_level_changed(self, _index: int) -> None:
        selected_level = self._level_combo.currentData()
        if selected_level is self._level:
            return
        self._level = selected_level
        self._max_number = _MAX_NUMBER_BY_LEVEL[selected_level]
        self._optimal_attempts = _optimal_attempts_for(self._max_number)
        ProgressTracker.set_level(_PROGRESS_KEY, selected_level)
        self.start()

    def _update_range_dependent_labels(self) -> None:
        self._instructions_label.setText(
            f"{MIN_NUMBER} ile {self._max_number} arasında bir sayı tuttum, bulabilir misin?"
        )
        self._guess_input.setPlaceholderText(f"{MIN_NUMBER}-{self._max_number} arası bir sayı")

    def _handle_guess(self) -> None:
        guess_value = self._parse_guess(self._guess_input.text().strip())
        if guess_value is None:
            self._feedback_label.setText(
                f"Lütfen {MIN_NUMBER}-{self._max_number} arasında geçerli bir sayı girin."
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
        if not (MIN_NUMBER <= value <= self._max_number):
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

        if self._attempt_count <= self._optimal_attempts + GOOD_ATTEMPTS_MARGIN:
            ProgressTracker.unlock_achievement(Achievement.NUMBER_GUESSING_GOOD_OR_BETTER)

    def _build_performance_note(self) -> str:
        if self._attempt_count <= self._optimal_attempts:
            return "Mükemmel! 🏆"
        if self._attempt_count <= self._optimal_attempts + GOOD_ATTEMPTS_MARGIN:
            return "İyi iş! 👍"
        return f"Buldun ama daha hızlı olabilirdi (optimal: {self._optimal_attempts} deneme). 🐢"

    def _update_attempts_label(self) -> None:
        self._attempts_label.setText(f"Deneme sayısı: {self._attempt_count}")
