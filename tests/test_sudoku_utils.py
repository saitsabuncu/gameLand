from utils.sudoku_utils import (
    GRID_SIZE,
    create_empty_grid,
    find_conflicting_cells,
    generate_puzzle,
    is_grid_complete,
    is_valid_placement,
)


def test_is_valid_placement_detects_row_conflict() -> None:
    grid = create_empty_grid()
    grid[0][0] = 5
    assert is_valid_placement(grid, 0, 3, 5) is False
    assert is_valid_placement(grid, 0, 3, 6) is True


def test_is_valid_placement_detects_column_conflict() -> None:
    grid = create_empty_grid()
    grid[0][0] = 5
    assert is_valid_placement(grid, 4, 0, 5) is False


def test_is_valid_placement_detects_box_conflict() -> None:
    grid = create_empty_grid()
    grid[0][0] = 5
    assert is_valid_placement(grid, 2, 2, 5) is False


def test_is_valid_placement_ignores_the_cell_itself() -> None:
    grid = create_empty_grid()
    grid[0][0] = 5
    assert is_valid_placement(grid, 0, 0, 5) is True


def test_find_conflicting_cells_row_and_column_are_independent() -> None:
    grid = create_empty_grid()
    grid[0][0] = 5
    grid[0][1] = 5  # row conflict with (0, 0)
    grid[3][0] = 5  # column conflict with (0, 0), not with (0, 1)
    conflicts = find_conflicting_cells(grid)
    assert (0, 0) in conflicts
    assert (0, 1) in conflicts
    assert (3, 0) in conflicts


def test_find_conflicting_cells_empty_grid_has_none() -> None:
    assert find_conflicting_cells(create_empty_grid()) == set()


def test_is_grid_complete() -> None:
    assert is_grid_complete(create_empty_grid()) is False
    assert is_grid_complete([[1] * GRID_SIZE for _ in range(GRID_SIZE)]) is True


def test_generate_puzzle_solution_is_valid_and_complete() -> None:
    generated = generate_puzzle(clue_count=40)
    assert is_grid_complete(generated.solution)
    assert find_conflicting_cells(generated.solution) == set()


def test_generate_puzzle_puzzle_cells_match_the_solution() -> None:
    generated = generate_puzzle(clue_count=40)
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            clue = generated.puzzle[row][col]
            if clue != 0:
                assert clue == generated.solution[row][col]


def test_generate_puzzle_never_removes_below_the_requested_clue_count() -> None:
    generated = generate_puzzle(clue_count=40)
    clue_count = sum(1 for row in generated.puzzle for value in row if value != 0)
    assert clue_count >= 40
