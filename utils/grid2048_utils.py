import random
from dataclasses import dataclass
from enum import Enum, auto
from typing import Final

GRID_SIZE: Final[int] = 4
WIN_TILE: Final[int] = 2048

SPAWN_VALUE_TWO: Final[int] = 2
SPAWN_VALUE_FOUR: Final[int] = 4
SPAWN_FOUR_PROBABILITY: Final[float] = 0.1

Grid = list[list[int]]


class Direction(Enum):
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()


@dataclass(frozen=True)
class MoveResult:
    grid: Grid
    score_gained: int
    moved: bool


def create_empty_grid(size: int = GRID_SIZE) -> Grid:
    return [[0] * size for _ in range(size)]


def spawn_random_tile(grid: Grid) -> bool:
    """Fills one random empty cell with a 2 (90%) or 4 (10%). Returns False
    if the grid has no empty cell to spawn into."""
    empty_cells = [
        (row, col) for row in range(len(grid)) for col in range(len(grid[row])) if grid[row][col] == 0
    ]
    if not empty_cells:
        return False
    row, col = random.choice(empty_cells)
    grid[row][col] = SPAWN_VALUE_FOUR if random.random() < SPAWN_FOUR_PROBABILITY else SPAWN_VALUE_TWO
    return True


def apply_move(grid: Grid, direction: Direction) -> MoveResult:
    """Slides and merges `grid` one step in `direction`.

    Every direction is implemented as the same left-slide-and-merge
    primitive (_merge_line) applied to a transformed view of the grid
    (transposed and/or row-reversed), then transformed back -- avoids
    writing four near-duplicate merge implementations.
    """
    working_grid = _orient_towards_left(grid, direction)

    merged_rows: list[list[int]] = []
    total_score_gained = 0
    for row in working_grid:
        merged_row, row_score = _merge_line(row)
        merged_rows.append(merged_row)
        total_score_gained += row_score

    new_grid = _orient_from_left(merged_rows, direction)
    return MoveResult(grid=new_grid, score_gained=total_score_gained, moved=new_grid != grid)


def has_any_moves(grid: Grid) -> bool:
    """True if an empty cell exists or any two orthogonal neighbors are equal."""
    size = len(grid)
    for row in range(size):
        for col in range(size):
            if grid[row][col] == 0:
                return True
            if col + 1 < size and grid[row][col] == grid[row][col + 1]:
                return True
            if row + 1 < size and grid[row][col] == grid[row + 1][col]:
                return True
    return False


def get_max_tile(grid: Grid) -> int:
    return max(value for row in grid for value in row)


def _merge_line(line: list[int]) -> tuple[list[int], int]:
    """Slides non-zero values to the left edge, merging equal neighbors
    once each (scanned left-to-right), and pads the rest with zeros."""
    compacted = [value for value in line if value != 0]
    merged: list[int] = []
    score_gained = 0

    index = 0
    while index < len(compacted):
        current = compacted[index]
        if index + 1 < len(compacted) and compacted[index + 1] == current:
            merged_value = current * 2
            merged.append(merged_value)
            score_gained += merged_value
            index += 2
        else:
            merged.append(current)
            index += 1

    merged.extend([0] * (len(line) - len(merged)))
    return merged, score_gained


def _orient_towards_left(grid: Grid, direction: Direction) -> Grid:
    if direction is Direction.LEFT:
        return [row[:] for row in grid]
    if direction is Direction.RIGHT:
        return _reverse_rows(grid)
    if direction is Direction.UP:
        return _transpose(grid)
    # Direction.DOWN
    return _reverse_rows(_transpose(grid))


def _orient_from_left(grid: Grid, direction: Direction) -> Grid:
    if direction is Direction.LEFT:
        return grid
    if direction is Direction.RIGHT:
        return _reverse_rows(grid)
    if direction is Direction.UP:
        return _transpose(grid)
    # Direction.DOWN
    return _transpose(_reverse_rows(grid))


def _transpose(grid: Grid) -> Grid:
    return [list(row) for row in zip(*grid)]


def _reverse_rows(grid: Grid) -> Grid:
    return [list(reversed(row)) for row in grid]
