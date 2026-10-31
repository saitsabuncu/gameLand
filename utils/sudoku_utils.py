import random
from dataclasses import dataclass
from typing import Final

GRID_SIZE: Final[int] = 9
BOX_SIZE: Final[int] = 3

# Target number of filled starting cells for the single fixed difficulty.
# The hole-digging generator may stop slightly above this if removing more
# cells would break the puzzle's unique solution.
MEDIUM_CLUE_COUNT: Final[int] = 40

# Uniqueness checks during generation only need to tell "exactly one" from
# "more than one" -- counting stops as soon as a second solution is found.
_UNIQUENESS_SOLUTION_LIMIT: Final[int] = 2

Grid = list[list[int]]


@dataclass(frozen=True)
class GeneratedPuzzle:
    puzzle: Grid
    solution: Grid


def create_empty_grid() -> Grid:
    return [[0] * GRID_SIZE for _ in range(GRID_SIZE)]


def is_valid_placement(grid: Grid, row: int, col: int, value: int) -> bool:
    """True if `value` could legally sit at (row, col): not already present
    elsewhere in the same row, column, or 3x3 box. Ignores grid[row][col]
    itself, so it also works to re-validate a cell that already holds a
    value."""
    for check_col in range(GRID_SIZE):
        if check_col != col and grid[row][check_col] == value:
            return False
    for check_row in range(GRID_SIZE):
        if check_row != row and grid[check_row][col] == value:
            return False

    box_row_start = (row // BOX_SIZE) * BOX_SIZE
    box_col_start = (col // BOX_SIZE) * BOX_SIZE
    for box_row in range(box_row_start, box_row_start + BOX_SIZE):
        for box_col in range(box_col_start, box_col_start + BOX_SIZE):
            if (box_row, box_col) != (row, col) and grid[box_row][box_col] == value:
                return False
    return True


def find_conflicting_cells(grid: Grid) -> set[tuple[int, int]]:
    """Returns every filled cell that currently breaks the row/column/box
    rule against another filled cell (both cells in a conflicting pair are
    included, for highlighting)."""
    conflicts: set[tuple[int, int]] = set()
    for row in range(GRID_SIZE):
        _mark_duplicates(grid, [(row, col) for col in range(GRID_SIZE)], conflicts)
    for col in range(GRID_SIZE):
        _mark_duplicates(grid, [(row, col) for row in range(GRID_SIZE)], conflicts)
    for box_row_start in range(0, GRID_SIZE, BOX_SIZE):
        for box_col_start in range(0, GRID_SIZE, BOX_SIZE):
            cells = [
                (box_row_start + r, box_col_start + c)
                for r in range(BOX_SIZE)
                for c in range(BOX_SIZE)
            ]
            _mark_duplicates(grid, cells, conflicts)
    return conflicts


def is_grid_complete(grid: Grid) -> bool:
    return all(value != 0 for row in grid for value in row)


def generate_puzzle(clue_count: int = MEDIUM_CLUE_COUNT) -> GeneratedPuzzle:
    """Generates a solved grid, then digs holes (removing cells one at a
    time in random order) while confirming after every removal that the
    puzzle still has exactly one solution -- a removal that would create a
    second solution is reverted and that clue stays."""
    solution = _generate_full_solution()
    puzzle = [row[:] for row in solution]

    cell_order = [(row, col) for row in range(GRID_SIZE) for col in range(GRID_SIZE)]
    random.shuffle(cell_order)

    cells_to_remove = GRID_SIZE * GRID_SIZE - clue_count
    removed_count = 0
    for row, col in cell_order:
        if removed_count >= cells_to_remove:
            break
        previous_value = puzzle[row][col]
        puzzle[row][col] = 0
        if _count_solutions([r[:] for r in puzzle], _UNIQUENESS_SOLUTION_LIMIT) == 1:
            removed_count += 1
        else:
            puzzle[row][col] = previous_value

    return GeneratedPuzzle(puzzle=puzzle, solution=solution)


def _mark_duplicates(
    grid: Grid, cells: list[tuple[int, int]], conflicts: set[tuple[int, int]]
) -> None:
    seen_at: dict[int, tuple[int, int]] = {}
    for row, col in cells:
        value = grid[row][col]
        if value == 0:
            continue
        if value in seen_at:
            conflicts.add((row, col))
            conflicts.add(seen_at[value])
        else:
            seen_at[value] = (row, col)


def _find_empty_cell(grid: Grid) -> tuple[int, int] | None:
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            if grid[row][col] == 0:
                return row, col
    return None


def _generate_full_solution() -> Grid:
    grid = create_empty_grid()
    _fill_grid_randomly(grid)
    return grid


def _fill_grid_randomly(grid: Grid) -> bool:
    """Randomized backtracking fill: shuffles candidate order at each empty
    cell so repeated calls produce different complete grids."""
    empty_cell = _find_empty_cell(grid)
    if empty_cell is None:
        return True

    row, col = empty_cell
    candidates = list(range(1, GRID_SIZE + 1))
    random.shuffle(candidates)
    for value in candidates:
        if is_valid_placement(grid, row, col, value):
            grid[row][col] = value
            if _fill_grid_randomly(grid):
                return True
            grid[row][col] = 0
    return False


def _count_solutions(grid: Grid, remaining_limit: int) -> int:
    """Counts solutions of `grid`, stopping as soon as `remaining_limit` is
    reached (mutates `grid` as scratch space during the search)."""
    empty_cell = _find_empty_cell(grid)
    if empty_cell is None:
        return 1

    row, col = empty_cell
    found = 0
    for value in range(1, GRID_SIZE + 1):
        if found >= remaining_limit:
            break
        if is_valid_placement(grid, row, col, value):
            grid[row][col] = value
            found += _count_solutions(grid, remaining_limit - found)
            grid[row][col] = 0
    return found
