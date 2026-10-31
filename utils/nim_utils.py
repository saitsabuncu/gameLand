import random


def compute_nim_sum(piles: list[int]) -> int:
    """XOR of all pile sizes.

    A nonzero nim-sum means the player about to move can force a win
    with optimal play; a zero nim-sum means it's a losing position
    against optimal counterplay.
    """
    nim_sum = 0
    for pile in piles:
        nim_sum ^= pile
    return nim_sum


def compute_optimal_move(piles: list[int]) -> tuple[int, int]:
    """Returns (pile_index, new_size) for an optimal normal-play Nim move.

    If a winning move exists (nim-sum != 0), returns the move that
    leaves the opponent facing a nim-sum of zero. Otherwise (the mover
    is already in a losing position), falls back to removing one stone
    from a random non-empty pile, since no move can force a win against
    optimal counterplay from here.
    """
    nim_sum = compute_nim_sum(piles)
    if nim_sum != 0:
        for index, size in enumerate(piles):
            target = size ^ nim_sum
            if target < size:
                return index, target

    non_empty_indices = [index for index, size in enumerate(piles) if size > 0]
    index = random.choice(non_empty_indices)
    return index, piles[index] - 1
