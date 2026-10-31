import math

import pytest

from utils.chaos_game_utils import (
    MIN_VERTEX_COUNT,
    Point,
    compute_polygon_vertices,
    pick_starting_point,
    step,
)


def test_compute_polygon_vertices_count_and_radius() -> None:
    center = Point(0.0, 0.0)
    vertices = compute_polygon_vertices(4, center, 10.0)
    assert len(vertices) == 4
    for vertex in vertices:
        distance = math.hypot(vertex.x - center.x, vertex.y - center.y)
        assert distance == pytest.approx(10.0)


def test_compute_polygon_vertices_first_point_is_straight_up() -> None:
    center = Point(5.0, 5.0)
    vertices = compute_polygon_vertices(3, center, 10.0)
    assert vertices[0].x == pytest.approx(center.x)
    assert vertices[0].y == pytest.approx(center.y - 10.0)


def test_pick_starting_point_returns_one_of_the_vertices() -> None:
    vertices = compute_polygon_vertices(5, Point(0.0, 0.0), 1.0)
    for _ in range(20):
        assert pick_starting_point(vertices) in vertices


def test_step_moves_exactly_halfway_to_the_chosen_vertex() -> None:
    vertices = [Point(0.0, 0.0), Point(10.0, 0.0), Point(0.0, 10.0)]
    current = Point(0.0, 0.0)
    new_point, chosen_index = step(current, vertices, None, None)
    target = vertices[chosen_index]
    assert new_point.x == pytest.approx((current.x + target.x) / 2)
    assert new_point.y == pytest.approx((current.y + target.y) / 2)


def test_step_unrestricted_for_a_triangle_allows_repeats() -> None:
    # With no restriction at MIN_VERTEX_COUNT, repeating the previous pick
    # must be possible -- run enough iterations that seeing it at least
    # once is a near-certainty rather than a claim about a single draw.
    vertices = compute_polygon_vertices(MIN_VERTEX_COUNT, Point(0.0, 0.0), 1.0)
    point = Point(0.0, 0.0)
    previous_index: int | None = None
    previous_previous_index: int | None = None
    repeat_seen = False
    for _ in range(200):
        point, chosen_index = step(point, vertices, previous_index, previous_previous_index)
        if chosen_index == previous_index:
            repeat_seen = True
            break
        previous_previous_index = previous_index
        previous_index = chosen_index
    assert repeat_seen


def test_step_restricted_never_repeats_either_of_the_last_two_picks() -> None:
    for vertex_count in (4, 5, 6):
        vertices = compute_polygon_vertices(vertex_count, Point(0.0, 0.0), 1.0)
        point = Point(0.0, 0.0)
        previous_index: int | None = None
        previous_previous_index: int | None = None
        for _ in range(200):
            point, chosen_index = step(point, vertices, previous_index, previous_previous_index)
            assert chosen_index != previous_index
            if previous_previous_index is not None:
                assert chosen_index != previous_previous_index
            previous_previous_index = previous_index
            previous_index = chosen_index
