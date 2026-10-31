from utils.grid2048_utils import (
    Direction,
    apply_move,
    create_empty_grid,
    get_max_tile,
    has_any_moves,
    spawn_random_tile,
)


def test_create_empty_grid_shape() -> None:
    grid = create_empty_grid(4)
    assert len(grid) == 4
    assert all(len(row) == 4 for row in grid)
    assert all(value == 0 for row in grid for value in row)


def test_spawn_random_tile_fills_one_empty_cell() -> None:
    grid = create_empty_grid(4)
    assert spawn_random_tile(grid) is True
    non_zero = sum(1 for row in grid for value in row if value != 0)
    assert non_zero == 1
    assert get_max_tile(grid) in (2, 4)


def test_spawn_random_tile_returns_false_when_full() -> None:
    grid = [[2] * 4 for _ in range(4)]
    assert spawn_random_tile(grid) is False


def test_apply_move_left_merges_and_slides() -> None:
    grid = [[2, 2, 0, 0]] + [[0, 0, 0, 0]] * 3
    result = apply_move(grid, Direction.LEFT)
    assert result.grid[0] == [4, 0, 0, 0]
    assert result.score_gained == 4
    assert result.moved is True


def test_apply_move_right_merges_towards_right_edge() -> None:
    grid = [[2, 2, 0, 0]] + [[0, 0, 0, 0]] * 3
    result = apply_move(grid, Direction.RIGHT)
    assert result.grid[0] == [0, 0, 0, 4]


def test_apply_move_up_and_down_merge_columns() -> None:
    grid = [[2, 0, 0, 0], [2, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]]

    up_result = apply_move(grid, Direction.UP)
    assert [row[0] for row in up_result.grid] == [4, 0, 0, 0]

    down_result = apply_move(grid, Direction.DOWN)
    assert [row[0] for row in down_result.grid] == [0, 0, 0, 4]


def test_apply_move_does_not_double_merge_in_one_pass() -> None:
    grid = [[2, 2, 2, 2]] + [[0, 0, 0, 0]] * 3
    result = apply_move(grid, Direction.LEFT)
    assert result.grid[0] == [4, 4, 0, 0]


def test_apply_move_reports_moved_false_when_nothing_changes() -> None:
    grid = [[2, 4, 8, 16]] + [[0, 0, 0, 0]] * 3
    result = apply_move(grid, Direction.LEFT)
    assert result.moved is False
    assert result.grid == grid


def test_has_any_moves_true_with_empty_cell() -> None:
    grid = [[2, 4, 8, 16], [4, 2, 4, 2], [2, 4, 2, 4], [4, 0, 4, 2]]
    assert has_any_moves(grid) is True


def test_has_any_moves_true_with_mergeable_neighbors() -> None:
    grid = [[2, 4, 8, 16], [4, 2, 4, 2], [2, 2, 2, 4], [4, 2, 4, 2]]
    assert has_any_moves(grid) is True


def test_has_any_moves_false_when_board_locked() -> None:
    grid = [
        [2, 4, 2, 4],
        [4, 2, 4, 2],
        [2, 4, 2, 4],
        [4, 2, 4, 2],
    ]
    assert has_any_moves(grid) is False


def test_get_max_tile() -> None:
    grid = [[2, 4], [128, 8]]
    assert get_max_tile(grid) == 128
