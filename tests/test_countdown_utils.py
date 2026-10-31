import pytest

from utils.countdown_utils import (
    CLOSE_POINTS,
    EXACT_POINTS,
    LARGE_NUMBERS,
    NEAR_POINTS,
    NUMBERS_PER_ROUND,
    TARGET_MAX,
    TARGET_MIN,
    InvalidExpressionError,
    draw_round_numbers,
    draw_target,
    evaluate_countdown_expression,
    extract_used_numbers,
    score_for_result,
    validate_numbers_used,
)


def test_draw_round_numbers_count_and_large_numbers_each_at_most_once() -> None:
    for _ in range(100):
        numbers = draw_round_numbers()
        assert len(numbers) == NUMBERS_PER_ROUND
        large_drawn = [value for value in numbers if value in LARGE_NUMBERS]
        assert len(large_drawn) == len(set(large_drawn))


def test_draw_round_numbers_small_values_at_most_twice() -> None:
    for _ in range(100):
        numbers = draw_round_numbers()
        for value in range(1, 11):
            assert numbers.count(value) <= 2


def test_draw_target_in_range() -> None:
    for _ in range(100):
        target = draw_target()
        assert TARGET_MIN <= target <= TARGET_MAX


@pytest.mark.parametrize(
    "target,result,expected",
    [
        (552, 552, EXACT_POINTS),
        (552, 550, CLOSE_POINTS),
        (552, 557, CLOSE_POINTS),
        (552, 545, NEAR_POINTS),
        (552, 562, NEAR_POINTS),
        (552, 500, 0),
    ],
)
def test_score_for_result(target: int, result: int, expected: int) -> None:
    assert score_for_result(target, result) == expected


def test_extract_used_numbers_returns_every_literal_as_a_multiset() -> None:
    # ast.walk() is breadth-first, not source order, so compare as a
    # multiset rather than asserting an exact left-to-right sequence.
    assert sorted(extract_used_numbers("(75 - 50) * 4 + 1")) == [1, 4, 50, 75]


def test_validate_numbers_used_allows_valid_usage() -> None:
    validate_numbers_used(used_numbers=[75, 50], available_numbers=[75, 50, 4, 1, 2, 2])


def test_validate_numbers_used_rejects_overuse() -> None:
    with pytest.raises(InvalidExpressionError):
        validate_numbers_used(used_numbers=[2, 2, 2], available_numbers=[2, 2, 1])


@pytest.mark.parametrize(
    "expression,expected",
    [
        ("75 - 50", 25),
        ("(75 - 50) * 4", 100),
        ("100 / 4", 25),
        ("1 + 2 + 3", 6),
    ],
)
def test_evaluate_countdown_expression_valid(expression: str, expected: int) -> None:
    assert evaluate_countdown_expression(expression) == expected


@pytest.mark.parametrize(
    "expression",
    [
        "5 - 10",  # negative intermediate result
        "5 / 2",  # non-exact division
        "5 ** 2",  # disallowed operator
        "True + 1",  # bool literal disguised as an int
        "not 1",  # disallowed node type
        "1 +",  # syntax error
    ],
)
def test_evaluate_countdown_expression_rejects_rule_violations(expression: str) -> None:
    with pytest.raises(InvalidExpressionError):
        evaluate_countdown_expression(expression)
