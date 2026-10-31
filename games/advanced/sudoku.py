from typing import Final

from PyQt6.QtCore import QRegularExpression, Qt
from PyQt6.QtGui import QRegularExpressionValidator
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from core.base_game import BaseGame, Difficulty, GameLevel
from core.game_registry import register_game
from core.progress_tracker import ProgressTracker
from utils.sudoku_utils import (
    GRID_SIZE,
    find_conflicting_cells,
    generate_puzzle,
    is_grid_complete,
)

CELL_SIZE_PX: Final[int] = 46
BOARD_MARGIN_PX: Final[int] = 14
MAX_HINTS: Final[int] = 3

# Key under which the player's last-picked GameLevel is saved via
# ProgressTracker -- a stable internal id, independent of display_name
# (which is user-facing and could change without this needing to).
_PROGRESS_KEY: Final[str] = "sudoku"

# The generator (utils/sudoku_utils.generate_puzzle) only has one lever for
# difficulty: how many clue cells are left after digging holes. This is a
# genuine, if blunt, difficulty proxy (fewer givens -> more deduction
# needed) -- it does NOT grade by which solving technique is required, so
# two "Zor" puzzles can vary in how hard they actually feel. Generation
# time grows as clue count drops (measured: ~10ms at 46, ~130ms at 32),
# still well under anything a player would notice.
_CLUE_COUNT_BY_LEVEL: Final[dict[GameLevel, int]] = {
    GameLevel.EASY: 46,
    GameLevel.MEDIUM: 40,
    GameLevel.HARD: 32,
}

_THIN_BORDER: Final[str] = "1px solid #c6c6c6"
_THICK_BORDER: Final[str] = "2px solid #2b2b2b"
_BOARD_CONTAINER_STYLE: Final[str] = (
    "#sudokuBoard { background-color: #fafafa; border: 2px solid #2b2b2b; border-radius: 6px; }"
)

_CLUE_STYLE: Final[tuple[str, str]] = ("#e8e8e8", "#222222")
_EMPTY_STYLE: Final[tuple[str, str]] = ("#ffffff", "#1a73e8")
_CONFLICT_STYLE: Final[tuple[str, str]] = ("#f8d7da", "#a71d2a")

_DIGIT_1_TO_9_VALIDATOR_PATTERN: Final[str] = "[1-9]"


@register_game(
    display_name="Sudoku",
    difficulty=Difficulty.ADVANCED,
    instructions=(
        "Klasik 9x9 Sudoku: her satırda, her sütunda ve her 3x3 kutuda "
        "1'den 9'a kadar her rakam tam olarak bir kez bulunmalı. Gri "
        "hücreler sabit ipuçları (değiştirilemez); boş bir hücreye "
        "tıklayıp klavyeden 1-9 yaz, silmek için Backspace/Delete "
        "kullan.\n\n"
        "Üstteki menüden Kolay/Orta/Zor seviyesini seçebilirsin -- "
        "seviye, başlangıçta bulmacada kaç hücrenin dolu (ipucu) "
        "bırakılacağını belirler: Kolay daha çok ipucu demek, Zor daha "
        "az. Seçtiğin seviye hatırlanır ve bir dahaki açılışta otomatik "
        "seçili gelir.\n\n"
        "Bir rakam, aynı satır/sütun/kutuda zaten varsa o hücre (ve "
        "çakıştığı hücre) anında kırmızıya döner -- hatanı hemen "
        f"görürsün. Toplam {MAX_HINTS} ipucu hakkın var: boş bir hücreye "
        "tıklayıp 'İpucu Ver'e basarsan o hücrenin doğru değeri otomatik "
        "yazılır. Tüm hücreler çakışmasız dolunca bulmaca tamamlanmış "
        "sayılır."
    ),
)
class SudokuGame(BaseGame):
    """Classic 9x9 Sudoku with instant conflict highlighting and limited hints.

    The puzzle is regenerated (new full solution + a fresh set of holes)
    every start()/reset(), always with a verified unique solution -- see
    utils/sudoku_utils.generate_puzzle(). Turn-based with no timer, so
    toggle_pause() is left as BaseGame's inherited no-op.

    GameLevel (Easy/Medium/Hard) picks the clue count passed to
    generate_puzzle(); the player's choice is loaded from and saved to
    ProgressTracker, so it's remembered across app restarts.
    """

    def __init__(self) -> None:
        super().__init__()
        self._grid: list[list[int]] = []
        self._solution_grid: list[list[int]] = []
        self._clue_mask: list[list[bool]] = []
        self._hints_remaining: int = MAX_HINTS
        self._is_complete: bool = False
        self._level: GameLevel = ProgressTracker.get_level(_PROGRESS_KEY, default=GameLevel.MEDIUM)

        self._level_combo = QComboBox()
        for level in GameLevel:
            self._level_combo.addItem(level.value, userData=level)
        self._level_combo.setCurrentIndex(self._level_combo.findData(self._level))
        self._level_combo.currentIndexChanged.connect(self._handle_level_changed)

        self._status_label = QLabel()
        self._status_label.setStyleSheet("font-size: 16px; font-weight: 600;")

        self._cells: list[list[QLineEdit]] = []
        self._cell_coordinates: dict[QLineEdit, tuple[int, int]] = {}

        board_container = QWidget()
        board_container.setObjectName("sudokuBoard")
        board_container.setStyleSheet(_BOARD_CONTAINER_STYLE)
        # Fixed size policy (QWidget's default) so the container -- and the
        # QGridLayout inside it -- sizes to its content instead of
        # stretching to fill the parent width, which would otherwise spread
        # the fixed-size cells apart with uneven gaps between columns.
        board_layout = QGridLayout(board_container)
        board_layout.setSpacing(0)
        board_layout.setContentsMargins(
            BOARD_MARGIN_PX, BOARD_MARGIN_PX, BOARD_MARGIN_PX, BOARD_MARGIN_PX
        )
        validator = QRegularExpressionValidator(QRegularExpression(_DIGIT_1_TO_9_VALIDATOR_PATTERN))

        for row in range(GRID_SIZE):
            cell_row: list[QLineEdit] = []
            for col in range(GRID_SIZE):
                cell = QLineEdit()
                cell.setFixedSize(CELL_SIZE_PX, CELL_SIZE_PX)
                cell.setAlignment(Qt.AlignmentFlag.AlignCenter)
                cell.setMaxLength(1)
                cell.setValidator(validator)
                cell.textChanged.connect(
                    lambda text, r=row, c=col: self._handle_cell_changed(r, c, text)
                )
                board_layout.addWidget(cell, row, col)
                cell_row.append(cell)
                self._cell_coordinates[cell] = (row, col)
            self._cells.append(cell_row)

        # Centers the (fixed-size) board horizontally regardless of the
        # game container's width, instead of letting it hug the left edge.
        board_centering_layout = QHBoxLayout()
        board_centering_layout.addStretch(1)
        board_centering_layout.addWidget(board_container)
        board_centering_layout.addStretch(1)

        self._hint_button = QPushButton()
        self._hint_button.setStyleSheet("padding: 6px 14px; font-size: 14px;")
        self._hint_button.clicked.connect(self._handle_hint_clicked)

        controls_layout = QHBoxLayout()
        controls_layout.addStretch(1)
        controls_layout.addWidget(self._hint_button)
        controls_layout.addStretch(1)

        level_layout = QHBoxLayout()
        level_layout.addStretch(1)
        level_layout.addWidget(QLabel("Seviye:"))
        level_layout.addWidget(self._level_combo)
        level_layout.addStretch(1)

        layout = QVBoxLayout(self)
        layout.addLayout(level_layout)
        layout.addSpacing(8)
        layout.addWidget(self._status_label, alignment=Qt.AlignmentFlag.AlignHCenter)
        layout.addSpacing(8)
        layout.addLayout(board_centering_layout)
        layout.addSpacing(12)
        layout.addLayout(controls_layout)
        layout.addStretch(1)

    def start(self) -> None:
        generated = generate_puzzle(clue_count=_CLUE_COUNT_BY_LEVEL[self._level])
        self._solution_grid = generated.solution
        self._grid = [row[:] for row in generated.puzzle]
        self._clue_mask = [[value != 0 for value in row] for row in generated.puzzle]
        self._hints_remaining = MAX_HINTS
        self._is_complete = False

        self._status_label.setText("Bulmacayı çöz! Boş bir hücreye tıkla ve 1-9 yaz.")
        self._update_hint_button()
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self._configure_cell(row, col)
        self._refresh_conflicts_and_completion()

    def reset(self) -> None:
        self.start()

    def _handle_level_changed(self, _index: int) -> None:
        selected_level = self._level_combo.currentData()
        if selected_level is self._level:
            return
        self._level = selected_level
        ProgressTracker.set_level(_PROGRESS_KEY, selected_level)
        self.start()

    def _configure_cell(self, row: int, col: int) -> None:
        cell = self._cells[row][col]
        value = self._grid[row][col]
        cell.blockSignals(True)
        cell.setText(str(value) if value else "")
        cell.blockSignals(False)

        is_clue = self._clue_mask[row][col]
        cell.setReadOnly(is_clue)
        cell.setFocusPolicy(Qt.FocusPolicy.NoFocus if is_clue else Qt.FocusPolicy.StrongFocus)

    def _handle_cell_changed(self, row: int, col: int, text: str) -> None:
        if self._is_complete:
            return
        self._grid[row][col] = int(text) if text else 0
        self._refresh_conflicts_and_completion()

    def _refresh_conflicts_and_completion(self) -> None:
        conflicting_cells = find_conflicting_cells(self._grid)
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self._style_cell(row, col, is_conflict=(row, col) in conflicting_cells)

        if not self._is_complete and is_grid_complete(self._grid) and not conflicting_cells:
            self._is_complete = True
            self._status_label.setText("🎉 Tebrikler! Bulmacayı doğru çözdün.")
            self._lock_all_cells()

    def _style_cell(self, row: int, col: int, is_conflict: bool) -> None:
        if is_conflict:
            background_color, text_color = _CONFLICT_STYLE
        elif self._clue_mask[row][col]:
            background_color, text_color = _CLUE_STYLE
        else:
            background_color, text_color = _EMPTY_STYLE

        top = _THICK_BORDER if row % 3 == 0 else _THIN_BORDER
        left = _THICK_BORDER if col % 3 == 0 else _THIN_BORDER
        right = _THICK_BORDER if col == GRID_SIZE - 1 else _THIN_BORDER
        bottom = _THICK_BORDER if row == GRID_SIZE - 1 else _THIN_BORDER

        self._cells[row][col].setStyleSheet(
            f"background-color: {background_color}; color: {text_color}; "
            f"border-top: {top}; border-left: {left}; "
            f"border-right: {right}; border-bottom: {bottom}; "
            "font-size: 19px; font-weight: 700;"
        )

    def _lock_all_cells(self) -> None:
        for row in range(GRID_SIZE):
            for col in range(GRID_SIZE):
                self._cells[row][col].setReadOnly(True)
                self._cells[row][col].setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._update_hint_button()

    def _handle_hint_clicked(self) -> None:
        if self._hints_remaining <= 0 or self._is_complete:
            return

        focused_widget = QApplication.focusWidget()
        coordinates = (
            self._cell_coordinates.get(focused_widget)
            if isinstance(focused_widget, QLineEdit)
            else None
        )
        if coordinates is None:
            self._status_label.setText("İpucu için önce boş bir hücreye tıkla.")
            return

        row, col = coordinates
        if self._grid[row][col] != 0:
            self._status_label.setText("Bu hücre zaten dolu -- boş bir hücre seç.")
            return

        correct_value = self._solution_grid[row][col]
        self._cells[row][col].setText(str(correct_value))  # triggers _handle_cell_changed
        self._hints_remaining -= 1
        self._update_hint_button()
        self._status_label.setText(
            f"İpucu kullanıldı: {row + 1}. satır, {col + 1}. sütun → {correct_value}."
        )

    def _update_hint_button(self) -> None:
        self._hint_button.setText(f"💡 İpucu Ver (Kalan: {self._hints_remaining})")
        self._hint_button.setEnabled(self._hints_remaining > 0 and not self._is_complete)
