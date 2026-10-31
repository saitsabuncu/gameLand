import random
from dataclasses import dataclass
from enum import Enum
from typing import Final

from PyQt6.QtWidgets import QLabel, QPushButton, QVBoxLayout

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from ui.shortcut_aware_line_edit import ShortcutAwareLineEdit

QUESTION_COUNT: Final[int] = 10
NUMBER_MIN: Final[int] = 1
NUMBER_MAX: Final[int] = 50

# Multiplication/division operands are kept within the classic times-table
# range: factors up to 50 (50x50=2500) would be unreasonable for mental
# math at Beginner level.
FACTOR_MIN: Final[int] = 2
FACTOR_MAX: Final[int] = 12


class Operator(Enum):
    ADDITION = "+"
    SUBTRACTION = "-"
    MULTIPLICATION = "×"
    DIVISION = "÷"


@dataclass(frozen=True)
class MathQuestion:
    left_operand: int
    right_operand: int
    operator: Operator
    correct_answer: int

    @property
    def prompt(self) -> str:
        return f"{self.left_operand} {self.operator.value} {self.right_operand} = ?"


def _generate_question() -> MathQuestion:
    operator = random.choice(list(Operator))

    if operator is Operator.ADDITION:
        left = random.randint(NUMBER_MIN, NUMBER_MAX)
        right = random.randint(NUMBER_MIN, NUMBER_MAX)
        return MathQuestion(left, right, operator, left + right)

    if operator is Operator.SUBTRACTION:
        left = random.randint(NUMBER_MIN, NUMBER_MAX)
        right = random.randint(NUMBER_MIN, left)  # non-negative result
        return MathQuestion(left, right, operator, left - right)

    if operator is Operator.MULTIPLICATION:
        left = random.randint(FACTOR_MIN, FACTOR_MAX)
        right = random.randint(FACTOR_MIN, FACTOR_MAX)
        return MathQuestion(left, right, operator, left * right)

    # DIVISION: constructed from a clean multiplication so the result is
    # always a whole number.
    right = random.randint(FACTOR_MIN, FACTOR_MAX)
    quotient = random.randint(FACTOR_MIN, FACTOR_MAX)
    left = right * quotient
    return MathQuestion(left, right, operator, quotient)


@register_game(display_name="Math Quiz Challenge", difficulty=Difficulty.BEGINNER)
class MathQuizGame(BaseGame):
    """A 10-question arithmetic quiz covering +, -, ×, ÷ with no time pressure."""

    def __init__(self) -> None:
        super().__init__()
        self._questions: list[MathQuestion] = []
        self._current_index: int = 0
        self._score: int = 0
        self._answered_count: int = 0
        self._awaiting_next_question: bool = False

        self._progress_label = QLabel()
        self._score_label = QLabel()
        self._question_label = QLabel()
        self._question_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self._feedback_label = QLabel()

        self._answer_input = ShortcutAwareLineEdit()
        self._answer_input.setPlaceholderText("Cevabını yaz")
        self._answer_input.returnPressed.connect(self._handle_primary_action)

        self._primary_button = QPushButton("Cevapla")
        self._primary_button.clicked.connect(self._handle_primary_action)

        layout = QVBoxLayout(self)
        layout.addWidget(self._progress_label)
        layout.addWidget(self._score_label)
        layout.addWidget(self._question_label)
        layout.addWidget(self._answer_input)
        layout.addWidget(self._primary_button)
        layout.addWidget(self._feedback_label)
        layout.addStretch(1)

    def start(self) -> None:
        self._questions = [_generate_question() for _ in range(QUESTION_COUNT)]
        self._current_index = 0
        self._score = 0
        self._answered_count = 0
        self._awaiting_next_question = False
        self._feedback_label.clear()
        self._primary_button.setText("Cevapla")
        self._update_score_label()
        self._show_current_question()

    def reset(self) -> None:
        self.start()

    def _show_current_question(self) -> None:
        question = self._questions[self._current_index]
        self._progress_label.setText(f"Soru {self._current_index + 1}/{QUESTION_COUNT}")
        self._question_label.setText(question.prompt)
        self._answer_input.clear()
        self._answer_input.setEnabled(True)
        self._answer_input.setFocus()

    def _handle_primary_action(self) -> None:
        if self._awaiting_next_question:
            self._advance_to_next_question()
        else:
            self._evaluate_answer()

    def _evaluate_answer(self) -> None:
        answer_value = self._parse_answer(self._answer_input.text().strip())
        if answer_value is None:
            self._feedback_label.setText("Lütfen geçerli bir sayı gir.")
            return

        question = self._questions[self._current_index]
        self._answered_count += 1
        if answer_value == question.correct_answer:
            self._score += 1
            self._feedback_label.setText("Doğru! ✅")
        else:
            self._feedback_label.setText(f"Yanlış. Doğru cevap: {question.correct_answer} ❌")

        self._update_score_label()
        self._answer_input.setEnabled(False)
        self._awaiting_next_question = True
        self._primary_button.setText(
            "Bitir"
            if self._current_index + 1 >= QUESTION_COUNT
            else "Sonraki Soru (Enter)"
        )

    def _advance_to_next_question(self) -> None:
        self._current_index += 1
        if self._current_index >= QUESTION_COUNT:
            self._show_final_summary()
            return

        self._awaiting_next_question = False
        self._primary_button.setText("Cevapla")
        self._feedback_label.clear()
        self._show_current_question()

    def _show_final_summary(self) -> None:
        self._progress_label.setText(f"Tamamlandı: {QUESTION_COUNT}/{QUESTION_COUNT}")
        self._question_label.setText(f"Quiz bitti! Skor: {self._score}/{QUESTION_COUNT}")
        self._feedback_label.clear()
        self._answer_input.setEnabled(False)
        self._primary_button.setEnabled(False)

    def _parse_answer(self, text: str) -> int | None:
        try:
            return int(text)
        except ValueError:
            return None

    def _update_score_label(self) -> None:
        self._score_label.setText(f"Skor: {self._score}/{self._answered_count}")
