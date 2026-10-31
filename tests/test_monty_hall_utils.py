import pytest

from utils.monty_hall_utils import (
    DOOR_COUNT,
    SimulationResult,
    pick_host_door,
    pick_random_door,
    remaining_switch_door,
    run_simulation,
)


def test_pick_random_door_in_range() -> None:
    for _ in range(100):
        assert 0 <= pick_random_door() < DOOR_COUNT


def test_pick_host_door_avoids_car_and_player_choice() -> None:
    for _ in range(100):
        host_door = pick_host_door(car_door=0, player_choice=1)
        assert host_door == 2  # the only door left when car=0, choice=1


def test_pick_host_door_when_player_already_picked_the_car() -> None:
    # Host has two goat doors to choose between here; over many trials both
    # must appear, and the car/choice door (0) must never be picked.
    results = {pick_host_door(car_door=0, player_choice=0) for _ in range(100)}
    assert results == {1, 2}


def test_remaining_switch_door_is_the_one_untouched_door() -> None:
    assert remaining_switch_door(player_choice=0, host_door=1) == 2
    assert remaining_switch_door(player_choice=2, host_door=0) == 1


def test_simulation_result_win_rates() -> None:
    result = SimulationResult(rounds=10, switch_wins=7, stay_wins=3)
    assert result.switch_win_rate == pytest.approx(0.7)
    assert result.stay_win_rate == pytest.approx(0.3)


def test_simulation_result_zero_rounds_does_not_divide_by_zero() -> None:
    result = SimulationResult(rounds=0, switch_wins=0, stay_wins=0)
    assert result.switch_win_rate == 0.0
    assert result.stay_win_rate == 0.0


def test_run_simulation_switch_wins_about_two_thirds() -> None:
    result = run_simulation(20_000)
    assert result.rounds == 20_000
    assert result.switch_wins + result.stay_wins == 20_000
    assert result.switch_win_rate == pytest.approx(2 / 3, abs=0.03)
