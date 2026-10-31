import pytest

from utils.nim_utils import compute_nim_sum, compute_optimal_move


@pytest.mark.parametrize(
    "piles,expected",
    [
        ([1, 2, 3], 0),
        ([3, 4, 5], 2),
        ([0, 0, 0], 0),
        ([7], 7),
    ],
)
def test_compute_nim_sum(piles: list[int], expected: int) -> None:
    assert compute_nim_sum(piles) == expected


def test_optimal_move_leaves_zero_nim_sum_when_winning() -> None:
    piles = [3, 4, 5]  # nim-sum 2: a winning position
    index, new_size = compute_optimal_move(piles)
    result = piles[:]
    result[index] = new_size
    assert compute_nim_sum(result) == 0
    assert new_size < piles[index]


def test_optimal_move_from_losing_position_removes_one_stone() -> None:
    piles = [1, 2, 3]  # nim-sum 0: a losing position, no move forces zero
    index, new_size = compute_optimal_move(piles)
    assert new_size == piles[index] - 1


def test_optimal_move_never_increases_a_pile() -> None:
    for _ in range(50):
        piles = [1, 3, 5, 7]
        index, new_size = compute_optimal_move(piles)
        assert 0 <= new_size < piles[index]
