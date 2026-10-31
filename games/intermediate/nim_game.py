import random
from typing import Final

from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLayout, QPushButton, QVBoxLayout

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from utils.nim_utils import compute_optimal_move

PILE_COUNT_MIN: Final[int] = 3
PILE_COUNT_MAX: Final[int] = 4
PILE_SIZE_MIN: Final[int] = 1
PILE_SIZE_MAX: Final[int] = 7

STONE_SYMBOL: Final[str] = "●"


@register_game(
    display_name="Nim Game",
    difficulty=Difficulty.INTERMEDIATE,
    instructions=(
        "Sırayla bir yığından istediğin kadar taş al (bir seferde sadece bir "
        "yığından). Son taşı alan kazanır. Bilgisayar her zaman matematiksel "
        "olarak en iyi hamleyi yapar (nim-sum/XOR stratejisi): eğer başlangıçtaki "
        "yığınların XOR'u sıfırsa o oyunu kazanamazsın, sıfır değilse doğru "
        "hamlelerle kazanabilirsin. İpucu: amacın, sıra bilgisayara geçtiğinde "
        "kalan yığınların XOR'unu sıfır bırakmak."
    ),
)
class NimGame(BaseGame):
    """Classic Nim (normal play): take the last stone to win.

    Played against a computer opponent that always plays optimally
    (nim-sum strategy), so beating it from a losing starting position
    is not possible -- only recognizing and holding a winning one is.
    """

    def __init__(self) -> None:
        super().__init__()
        self._piles: list[int] = []
        self._is_player_turn: bool = True
        self._game_over: bool = False

        self._instructions_label = QLabel(
            "Sırayla bir yığından taş al. Bir taşa tıklarsan, o taş ve "
            "sağındaki tüm taşlar alınır. Son taşı alan kazanır!"
        )
        self._status_label = QLabel()
        self._result_label = QLabel()
        self._result_label.setStyleSheet("font-size: 18px; font-weight: 600;")

        self._board_layout = QVBoxLayout()

        layout = QVBoxLayout(self)
        layout.addWidget(self._instructions_label)
        layout.addWidget(self._status_label)
        layout.addLayout(self._board_layout)
        layout.addWidget(self._result_label)
        layout.addStretch(1)

    def start(self) -> None:
        pile_count = random.randint(PILE_COUNT_MIN, PILE_COUNT_MAX)
        self._piles = [random.randint(PILE_SIZE_MIN, PILE_SIZE_MAX) for _ in range(pile_count)]
        self._is_player_turn = True
        self._game_over = False
        self._result_label.clear()
        self._update_status_label()
        self._rebuild_board()

    def reset(self) -> None:
        self.start()

    def _update_status_label(self) -> None:
        if self._game_over:
            self._status_label.clear()
            return
        self._status_label.setText(
            "Sıra sende! 🎯" if self._is_player_turn else "Bilgisayar oynuyor... 💻"
        )

    def _rebuild_board(self) -> None:
        self._clear_layout(self._board_layout)
        for pile_index, pile_size in enumerate(self._piles):
            row_layout = QHBoxLayout()
            row_layout.addWidget(QLabel(f"Yığın {pile_index + 1}:"))
            for stone_index in range(pile_size):
                stone_button = QPushButton(STONE_SYMBOL)
                stone_button.setFixedSize(32, 32)
                stone_button.setEnabled(self._is_player_turn and not self._game_over)
                stone_button.clicked.connect(
                    lambda _checked, p=pile_index, s=stone_index: self._handle_stone_clicked(p, s)
                )
                row_layout.addWidget(stone_button)
            row_layout.addStretch(1)
            self._board_layout.addLayout(row_layout)

    def _clear_layout(self, layout: QLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()
                continue
            sub_layout = item.layout()
            if sub_layout is not None:
                self._clear_layout(sub_layout)

    def _handle_stone_clicked(self, pile_index: int, stone_index: int) -> None:
        if not self._is_player_turn or self._game_over:
            return

        self._piles[pile_index] = stone_index
        if self._check_game_over(won_by_player=True):
            return

        self._is_player_turn = False
        self._perform_ai_move()
        if self._check_game_over(won_by_player=False):
            return

        self._is_player_turn = True
        self._update_status_label()
        self._rebuild_board()

    def _perform_ai_move(self) -> None:
        pile_index, new_size = compute_optimal_move(self._piles)
        self._piles[pile_index] = new_size

    def _check_game_over(self, won_by_player: bool) -> bool:
        if any(pile > 0 for pile in self._piles):
            return False
        self._game_over = True
        self._result_label.setText(
            "Kazandın! 🎉 Son taşı sen aldın."
            if won_by_player
            else "Kaybettin! 💻 Bilgisayar son taşı aldı."
        )
        self._update_status_label()
        self._rebuild_board()
        return True
