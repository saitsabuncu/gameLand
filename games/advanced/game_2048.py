from typing import Final

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtWidgets import QGridLayout, QLabel, QVBoxLayout

from core.base_game import BaseGame, Difficulty
from core.game_registry import register_game
from utils.grid2048_utils import (
    Direction,
    Grid,
    apply_move,
    create_empty_grid,
    get_max_tile,
    has_any_moves,
    spawn_random_tile,
)

INITIAL_TILE_COUNT: Final[int] = 2
TILE_SIZE_PX: Final[int] = 70

# Classic 2048 tile palette: value -> (background, text color). A tile
# value not listed here (anything past 2048) falls back to _FALLBACK_STYLE.
_TILE_STYLES: Final[dict[int, tuple[str, str]]] = {
    0: ("#cdc1b4", "#cdc1b4"),
    2: ("#eee4da", "#776e65"),
    4: ("#ede0c8", "#776e65"),
    8: ("#f2b179", "#f9f6f2"),
    16: ("#f59563", "#f9f6f2"),
    32: ("#f67c5f", "#f9f6f2"),
    64: ("#f65e3b", "#f9f6f2"),
    128: ("#edcf72", "#f9f6f2"),
    256: ("#edcc61", "#f9f6f2"),
    512: ("#edc850", "#f9f6f2"),
    1024: ("#edc53f", "#f9f6f2"),
    2048: ("#edc22e", "#f9f6f2"),
}
_FALLBACK_STYLE: Final[tuple[str, str]] = ("#3c3a32", "#f9f6f2")

_DIRECTION_KEYS: Final[dict[Qt.Key, Direction]] = {
    Qt.Key.Key_Up: Direction.UP,
    Qt.Key.Key_Down: Direction.DOWN,
    Qt.Key.Key_Left: Direction.LEFT,
    Qt.Key.Key_Right: Direction.RIGHT,
}


@register_game(
    display_name="2048",
    difficulty=Difficulty.ADVANCED,
    instructions=(
        "Ok tuşlarıyla (↑ ↓ ← →) tüm taşları aynı yönde kaydır. Kaydırma "
        "sırasında aynı değerdeki komşu taşlar birleşip değerleri toplanır "
        "(iki '2' birleşince '4' olur). Her hamleden sonra boş bir hücreye "
        "yeni bir taş (%90 '2', %10 '4') eklenir.\n\n"
        "2048 değerine ulaştığında tebrik mesajı görürsün ama oyun bitmez -- "
        "istersen daha yüksek taşlar için devam edebilirsin. Oyun ancak grid "
        "tamamen dolup artık hiçbir yönde geçerli bir hamle (boş hücre ya da "
        "birleşebilecek komşu taş) kalmayınca biter."
    ),
)
class Game2048(BaseGame):
    """Classic 2048: slide-and-merge on a fixed 4x4 grid, arrow-key controls.

    No win-stops-the-game rule -- reaching the 2048 tile only shows a
    one-time banner; play continues until the board is genuinely stuck.
    Turn-based with no timer, so toggle_pause() is left as BaseGame's
    inherited no-op (same as Nim Game / Monty Hall).
    """

    def __init__(self) -> None:
        super().__init__()
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self._grid: Grid = create_empty_grid()
        self._score: int = 0
        self._game_over: bool = False
        self._has_shown_win_banner: bool = False

        self._score_label = QLabel()
        self._score_label.setStyleSheet("font-size: 16px; font-weight: 600;")
        self._status_label = QLabel()

        self._tile_labels: list[list[QLabel]] = []
        board_layout = QGridLayout()
        board_layout.setSpacing(6)
        for row_index in range(len(self._grid)):
            label_row: list[QLabel] = []
            for col_index in range(len(self._grid)):
                tile_label = QLabel()
                tile_label.setFixedSize(TILE_SIZE_PX, TILE_SIZE_PX)
                tile_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                board_layout.addWidget(tile_label, row_index, col_index)
                label_row.append(tile_label)
            self._tile_labels.append(label_row)

        layout = QVBoxLayout(self)
        layout.addWidget(self._score_label)
        layout.addLayout(board_layout)
        layout.addWidget(self._status_label)
        layout.addStretch(1)

    def start(self) -> None:
        self._grid = create_empty_grid()
        for _ in range(INITIAL_TILE_COUNT):
            spawn_random_tile(self._grid)
        self._score = 0
        self._game_over = False
        self._has_shown_win_banner = False
        self._status_label.clear()
        self._render_grid()
        self._update_score_label()
        self.setFocus()

    def reset(self) -> None:
        self.start()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        direction = _DIRECTION_KEYS.get(Qt.Key(event.key()))
        if direction is None or self._game_over:
            super().keyPressEvent(event)
            return
        self._handle_move(direction)

    def _handle_move(self, direction: Direction) -> None:
        result = apply_move(self._grid, direction)
        if not result.moved:
            return  # Nothing shifted in this direction; no new tile, no state change.

        self._grid = result.grid
        self._score += result.score_gained
        spawn_random_tile(self._grid)
        self._render_grid()
        self._update_score_label()
        self._check_win_condition()
        self._check_game_over_condition()

    def _check_win_condition(self) -> None:
        if self._has_shown_win_banner:
            return
        if get_max_tile(self._grid) >= 2048:
            self._has_shown_win_banner = True
            self._status_label.setText(
                "🎉 2048'e ulaştın! Daha yüksek taşlar için oynamaya devam edebilirsin."
            )

    def _check_game_over_condition(self) -> None:
        if has_any_moves(self._grid):
            return
        self._game_over = True
        self._status_label.setText(
            f"Oyun bitti! Hamle kalmadı. Maksimum taş: {get_max_tile(self._grid)}, "
            f"Skor: {self._score}"
        )

    def _render_grid(self) -> None:
        for row_index, row in enumerate(self._grid):
            for col_index, value in enumerate(row):
                label = self._tile_labels[row_index][col_index]
                label.setText(str(value) if value else "")
                background_color, text_color = _TILE_STYLES.get(value, _FALLBACK_STYLE)
                label.setStyleSheet(
                    f"background-color: {background_color}; color: {text_color}; "
                    "font-size: 20px; font-weight: 700; border-radius: 4px;"
                )

    def _update_score_label(self) -> None:
        self._score_label.setText(f"Skor: {self._score}")
