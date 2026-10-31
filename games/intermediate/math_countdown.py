from enum import Enum, auto
from typing import Final

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from ui.shortcut_aware_line_edit import ShortcutAwareLineEdit
from utils.countdown_utils import (
    InvalidExpressionError,
    draw_round_numbers,
    draw_target,
    evaluate_countdown_expression,
    extract_used_numbers,
    score_for_result,
    validate_numbers_used,
)

ROUND_COUNT: Final[int] = 5
ROUND_SECONDS: Final[int] = 30
TIMER_INTERVAL_MS: Final[int] = 1_000

MAX_POINTS_PER_ROUND: Final[int] = 10
MAX_TOTAL_SCORE: Final[int] = ROUND_COUNT * MAX_POINTS_PER_ROUND
GREAT_SCORE_RATIO: Final[float] = 0.8
GOOD_SCORE_RATIO: Final[float] = 0.6


class _RoundPhase(Enum):
    ACTIVE = auto()
    PAUSED = auto()
    ROUND_RESULT = auto()
    FINISHED = auto()


@register_game(
    display_name="Math Countdown",
    difficulty=Difficulty.INTERMEDIATE,
    instructions=(
        f"Klasik 'Countdown' sayı oyunu: her turda 6 sayı (büyük kartlar: 25, "
        "50, 75, 100 / küçük kartlar: 1-10, her biri iki kez) ve 3 haneli bir "
        "hedef sayı verilir. Elindeki sayıları (her birini en fazla elinde "
        "olduğu kadar) toplama, çıkarma, çarpma, bölme ve parantezlerle "
        f"birleştirip hedefe {ROUND_SECONDS} saniye içinde olabildiğince "
        "yaklaş. Tüm sayıları kullanmak zorunda değilsin.\n\n"
        "Kural: her ara işlem sonucu pozitif bir tam sayı olmalı (negatif, "
        "sıfır veya küsuratlı ara sonuca izin yok) ve bölme ancak kalansız "
        "bölünüyorsa yapılabilir.\n\n"
        f"Puanlama: tam isabet {MAX_POINTS_PER_ROUND} puan, fark 5 veya "
        "altıysa 7 puan, 10 veya altıysa 5 puan, daha uzaksa 0 puan. Süre "
        f"dolarsa o tur otomatik 0 puan olur. {ROUND_COUNT} tur "
        "sonunda toplam puanına göre bir değerlendirme görürsün.\n\n"
        "'P' tuşu zamanlayıcıyı duraklatır/devam ettirir."
    ),
)
class MathCountdownGame(BaseGame):
    """Classic Countdown numbers round: hit a 3-digit target with 6 cards.

    toggle_pause() genuinely pauses/resumes the per-round QTimer, unlike
    the other registered games where it's an inherited no-op -- this is
    the first timer-driven game, as anticipated in BaseGame's docstring.
    """

    def __init__(self) -> None:
        super().__init__()
        self._phase: _RoundPhase = _RoundPhase.FINISHED
        self._round_index: int = 0
        self._total_score: int = 0
        self._numbers: list[int] = []
        self._target: int = 0
        self._remaining_seconds: int = ROUND_SECONDS

        self._timer = QTimer(self)
        self._timer.setInterval(TIMER_INTERVAL_MS)
        self._timer.timeout.connect(self._handle_tick)

        self._progress_label = QLabel()
        self._timer_label = QLabel()
        self._score_label = QLabel()
        self._numbers_label = QLabel()
        self._numbers_label.setStyleSheet("font-size: 20px; font-weight: 600;")
        self._target_label = QLabel()
        self._target_label.setStyleSheet("font-size: 18px; font-weight: 600;")
        self._feedback_label = QLabel()

        self._expression_input = ShortcutAwareLineEdit()
        self._expression_input.setPlaceholderText("Örn. (75 - 50) * 4 + 1")
        self._expression_input.returnPressed.connect(self._handle_primary_action)

        self._primary_button = QPushButton("Gönder")
        self._primary_button.clicked.connect(self._handle_primary_action)

        header_layout = QHBoxLayout()
        header_layout.addWidget(self._progress_label)
        header_layout.addStretch(1)
        header_layout.addWidget(self._timer_label)

        layout = QVBoxLayout(self)
        layout.addLayout(header_layout)
        layout.addWidget(self._score_label)
        layout.addWidget(self._numbers_label)
        layout.addWidget(self._target_label)
        layout.addWidget(self._expression_input)
        layout.addWidget(self._primary_button)
        layout.addWidget(self._feedback_label)
        layout.addStretch(1)

    def start(self) -> None:
        self._round_index = 0
        self._total_score = 0
        self._update_score_label()
        self._begin_round()

    def reset(self) -> None:
        self._timer.stop()
        self.start()

    def toggle_pause(self) -> None:
        if self._phase == _RoundPhase.ACTIVE:
            self._phase = _RoundPhase.PAUSED
            self._timer.stop()
            self._set_input_enabled(False)
            self._timer_label.setText(f"⏸ Duraklatıldı ({self._remaining_seconds}s)")
        elif self._phase == _RoundPhase.PAUSED:
            self._phase = _RoundPhase.ACTIVE
            self._timer.start()
            self._set_input_enabled(True)
            self._expression_input.setFocus()
            self._update_timer_label()

    def _begin_round(self) -> None:
        self._round_index += 1
        self._numbers = draw_round_numbers()
        self._target = draw_target()
        self._remaining_seconds = ROUND_SECONDS
        self._phase = _RoundPhase.ACTIVE

        self._progress_label.setText(f"Tur {self._round_index}/{ROUND_COUNT}")
        self._numbers_label.setText("Sayılar: " + "   ".join(str(n) for n in self._numbers))
        self._target_label.setText(f"Hedef: {self._target}")
        self._feedback_label.clear()
        self._expression_input.clear()
        self._set_input_enabled(True)
        self._expression_input.setFocus()
        self._primary_button.setText("Gönder")
        self._update_timer_label()
        self._timer.start()

    def _handle_tick(self) -> None:
        self._remaining_seconds -= 1
        if self._remaining_seconds <= 0:
            self._timer.stop()
            self._finish_round(expression=self._expression_input.text().strip(), timed_out=True)
            return
        self._update_timer_label()

    def _handle_primary_action(self) -> None:
        if self._phase == _RoundPhase.ACTIVE:
            self._timer.stop()
            self._finish_round(expression=self._expression_input.text().strip(), timed_out=False)
        elif self._phase == _RoundPhase.ROUND_RESULT:
            self._advance_to_next_round()

    def _finish_round(self, expression: str, timed_out: bool) -> None:
        self._phase = _RoundPhase.ROUND_RESULT
        points, feedback = self._evaluate_submission(expression, timed_out)
        self._total_score += points
        self._update_score_label()
        self._feedback_label.setText(feedback)
        self._set_input_enabled(False)
        self._primary_button.setText(
            "Bitir" if self._round_index >= ROUND_COUNT else "Sonraki Tur (Enter)"
        )

    def _evaluate_submission(self, expression: str, timed_out: bool) -> tuple[int, str]:
        if not expression:
            reason = "süre doldu, cevap girilmedi" if timed_out else "boş cevap"
            return 0, f"⏰ {reason.capitalize()}. Hedef {self._target}'tı. +0 puan"

        try:
            used_numbers = extract_used_numbers(expression)
            validate_numbers_used(used_numbers, self._numbers)
            result = evaluate_countdown_expression(expression)
        except InvalidExpressionError as error:
            prefix = "⏰ Süre doldu, geçersiz ifade: " if timed_out else "❌ Geçersiz: "
            return 0, f"{prefix}{error} +0 puan"

        points = score_for_result(self._target, result)
        timeout_note = " (süre tam bu anda doldu)" if timed_out else ""
        return points, (
            f"{expression} = {result} -- hedef {self._target}, fark "
            f"{abs(self._target - result)}{timeout_note}. +{points} puan"
        )

    def _advance_to_next_round(self) -> None:
        if self._round_index >= ROUND_COUNT:
            self._show_final_summary()
            return
        self._begin_round()

    def _show_final_summary(self) -> None:
        self._phase = _RoundPhase.FINISHED
        self._progress_label.setText(f"Tamamlandı: {ROUND_COUNT}/{ROUND_COUNT}")
        self._feedback_label.setText(
            f"Oyun bitti! Toplam puan: {self._total_score}/{MAX_TOTAL_SCORE} "
            f"— {self._build_performance_note()}"
        )
        self._timer_label.clear()
        self._numbers_label.clear()
        self._target_label.clear()
        self._primary_button.setEnabled(False)

    def _build_performance_note(self) -> str:
        if self._total_score == MAX_TOTAL_SCORE:
            return "Mükemmel! 🏆"
        if self._total_score >= MAX_TOTAL_SCORE * GREAT_SCORE_RATIO:
            return "Harika iş! 🌟"
        if self._total_score >= MAX_TOTAL_SCORE * GOOD_SCORE_RATIO:
            return "İyi, ama daha pratik yapabilirsin. 👍"
        return "Daha çok pratik yapmalısın. 💪"

    def _set_input_enabled(self, enabled: bool) -> None:
        self._expression_input.setEnabled(enabled)
        self._primary_button.setEnabled(enabled or self._phase == _RoundPhase.ROUND_RESULT)

    def _update_score_label(self) -> None:
        self._score_label.setText(f"Toplam Puan: {self._total_score}/{MAX_TOTAL_SCORE}")

    def _update_timer_label(self) -> None:
        self._timer_label.setText(f"⏱ {self._remaining_seconds}s")
