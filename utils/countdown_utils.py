import ast
import random
from collections import Counter
from typing import Final

LARGE_NUMBERS: Final[tuple[int, ...]] = (25, 50, 75, 100)
# Each of 1..10 appears twice, matching the classic show's small-number deck.
SMALL_NUMBERS_POOL: Final[tuple[int, ...]] = tuple(range(1, 11)) * 2

NUMBERS_PER_ROUND: Final[int] = 6
LARGE_COUNT_MIN: Final[int] = 0
LARGE_COUNT_MAX: Final[int] = 4

TARGET_MIN: Final[int] = 101
TARGET_MAX: Final[int] = 999

EXACT_POINTS: Final[int] = 10
CLOSE_POINTS: Final[int] = 7
CLOSE_THRESHOLD: Final[int] = 5
NEAR_POINTS: Final[int] = 5
NEAR_THRESHOLD: Final[int] = 10

_ALLOWED_BINOP_TYPES: Final[tuple[type[ast.operator], ...]] = (
    ast.Add,
    ast.Sub,
    ast.Mult,
    ast.Div,
)


class InvalidExpressionError(Exception):
    """Raised when a submitted expression breaks Countdown's rules.

    Covers both syntax problems and rule violations (non-integer or
    non-positive intermediate results, disallowed operators/nodes).
    The message is written to be shown to the player as-is.
    """


def draw_round_numbers() -> list[int]:
    """Draws 6 numbers for a round: 0-4 large cards (25/50/75/100, each at
    most once) plus small cards (1-10, each at most twice) filling the rest.
    """
    large_count = random.randint(LARGE_COUNT_MIN, LARGE_COUNT_MAX)
    small_count = NUMBERS_PER_ROUND - large_count
    numbers = random.sample(LARGE_NUMBERS, large_count) + random.sample(
        SMALL_NUMBERS_POOL, small_count
    )
    random.shuffle(numbers)
    return numbers


def draw_target() -> int:
    """Returns a random 3-digit target in [TARGET_MIN, TARGET_MAX]."""
    return random.randint(TARGET_MIN, TARGET_MAX)


def score_for_result(target: int, result: int) -> int:
    """Classic Countdown scoring: closer misses still earn partial credit."""
    difference = abs(target - result)
    if difference == 0:
        return EXACT_POINTS
    if difference <= CLOSE_THRESHOLD:
        return CLOSE_POINTS
    if difference <= NEAR_THRESHOLD:
        return NEAR_POINTS
    return 0


def _parse(expression: str) -> ast.Expression:
    try:
        return ast.parse(expression, mode="eval")
    except SyntaxError as error:
        raise InvalidExpressionError("İfade ayrıştırılamadı, sözdizimini kontrol et.") from error


def extract_used_numbers(expression: str) -> list[int]:
    """Returns every integer literal appearing in `expression`, in order."""
    tree = _parse(expression)
    numbers: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and _is_plain_int(node.value):
            numbers.append(node.value)
    return numbers


def validate_numbers_used(used_numbers: list[int], available_numbers: list[int]) -> None:
    """Raises if `used_numbers` uses any value more often than it was drawn."""
    used_counts = Counter(used_numbers)
    available_counts = Counter(available_numbers)
    for value, used_count in used_counts.items():
        if used_count > available_counts.get(value, 0):
            raise InvalidExpressionError(f"{value} sayısını elindekinden fazla kullandın.")


def evaluate_countdown_expression(expression: str) -> int:
    """Evaluates `expression` under Countdown rules and returns the result.

    Only +, -, *, / and parentheses over integer literals are allowed.
    Every intermediate result must be a positive integer: subtraction may
    not reach zero or below, and division must divide evenly.
    """
    tree = _parse(expression)
    return _evaluate_node(tree.body)


def _is_plain_int(value: object) -> bool:
    # bool is a subclass of int in Python; exclude it so "True"/"False"
    # literals can't sneak in as 1/0.
    return isinstance(value, int) and not isinstance(value, bool)


def _evaluate_node(node: ast.AST) -> int:
    if isinstance(node, ast.Constant):
        if not _is_plain_int(node.value):
            raise InvalidExpressionError("Sadece tam sayılar kullanılabilir.")
        return node.value

    if isinstance(node, ast.BinOp):
        if not isinstance(node.op, _ALLOWED_BINOP_TYPES):
            raise InvalidExpressionError("Sadece +, -, *, / işlemlerine izin verilir.")
        left_value = _evaluate_node(node.left)
        right_value = _evaluate_node(node.right)
        return _apply_operator(node.op, left_value, right_value)

    raise InvalidExpressionError(
        "Geçersiz ifade: sadece sayılar, parantezler ve + - * / kullanabilirsin."
    )


def _apply_operator(operator: ast.operator, left: int, right: int) -> int:
    if isinstance(operator, ast.Add):
        return left + right
    if isinstance(operator, ast.Sub):
        result = left - right
        if result <= 0:
            raise InvalidExpressionError("Ara sonuç sıfır veya negatif olamaz.")
        return result
    if isinstance(operator, ast.Mult):
        return left * right

    # ast.Div: only the remaining allowed type at this point.
    if right == 0 or left % right != 0:
        raise InvalidExpressionError("Bölme sonucu tam sayı olmalı (kalansız bölünmeli).")
    return left // right
