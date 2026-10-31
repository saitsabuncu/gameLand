import math
import random
from dataclasses import dataclass
from typing import Final

MIN_VERTEX_COUNT: Final[int] = 3
MAX_VERTEX_COUNT: Final[int] = 6
MIDPOINT_RATIO: Final[float] = 0.5


@dataclass(frozen=True)
class Point:
    x: float
    y: float


def compute_polygon_vertices(vertex_count: int, center: Point, radius: float) -> list[Point]:
    """Returns `vertex_count` points evenly spaced on a circle of `radius`
    around `center`, starting straight up and proceeding clockwise."""
    start_angle = -math.pi / 2  # straight up
    vertices: list[Point] = []
    for index in range(vertex_count):
        angle = start_angle + (2 * math.pi * index / vertex_count)
        vertices.append(
            Point(center.x + radius * math.cos(angle), center.y + radius * math.sin(angle))
        )
    return vertices


def pick_starting_point(vertices: list[Point]) -> Point:
    """Any point works as a seed since the fractal attractor is reached
    within a handful of iterations regardless of start; a random vertex
    keeps this trivially inside the polygon with zero extra math."""
    return random.choice(vertices)


def step(
    current_point: Point,
    vertices: list[Point],
    previous_index: int | None,
    previous_previous_index: int | None,
) -> tuple[Point, int]:
    """Runs one Chaos Game iteration: picks the next target vertex under
    the restriction rule, moves `current_point` MIDPOINT_RATIO of the way
    towards it, and returns (new_point, chosen_vertex_index).

    Restriction rule: for a triangle (3 vertices), any vertex may be
    picked -- that unrestricted randomness is exactly what produces the
    Sierpinski triangle. For 4+ vertices, picking fully at random just
    fills the polygon solid with no visible structure, so the next choice
    is barred from repeating either of the last two distinct picks, which
    is enough to force a self-similar, non-uniform pattern to emerge.
    """
    vertex_count = len(vertices)
    chosen_index = _choose_next_vertex_index(vertex_count, previous_index, previous_previous_index)
    target = vertices[chosen_index]
    new_point = Point(
        current_point.x + (target.x - current_point.x) * MIDPOINT_RATIO,
        current_point.y + (target.y - current_point.y) * MIDPOINT_RATIO,
    )
    return new_point, chosen_index


def _choose_next_vertex_index(
    vertex_count: int, previous_index: int | None, previous_previous_index: int | None
) -> int:
    while True:
        candidate = random.randrange(vertex_count)
        if _is_candidate_allowed(vertex_count, candidate, previous_index, previous_previous_index):
            return candidate


def _is_candidate_allowed(
    vertex_count: int,
    candidate: int,
    previous_index: int | None,
    previous_previous_index: int | None,
) -> bool:
    if vertex_count == MIN_VERTEX_COUNT:
        return True
    return candidate != previous_index and candidate != previous_previous_index
