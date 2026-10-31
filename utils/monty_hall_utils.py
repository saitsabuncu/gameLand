import random
from dataclasses import dataclass
from typing import Final

DOOR_COUNT: Final[int] = 3


@dataclass(frozen=True)
class SimulationResult:
    """Aggregate outcome of running many independent Monty Hall trials."""

    rounds: int
    switch_wins: int
    stay_wins: int

    @property
    def switch_win_rate(self) -> float:
        return self.switch_wins / self.rounds if self.rounds else 0.0

    @property
    def stay_win_rate(self) -> float:
        return self.stay_wins / self.rounds if self.rounds else 0.0


def pick_random_door() -> int:
    """Returns a door index in [0, DOOR_COUNT)."""
    return random.randrange(DOOR_COUNT)


def pick_host_door(car_door: int, player_choice: int) -> int:
    """Returns the goat door the host opens: classic Monty Hall rule --
    the host never reveals the car and never opens the player's own pick.
    """
    candidates = [door for door in range(DOOR_COUNT) if door != car_door and door != player_choice]
    return random.choice(candidates)


def remaining_switch_door(player_choice: int, host_door: int) -> int:
    """Returns the single unopened door left to switch to."""
    for door in range(DOOR_COUNT):
        if door != player_choice and door != host_door:
            return door
    raise ValueError("No door left to switch to")  # unreachable while DOOR_COUNT == 3


def run_simulation(rounds: int) -> SimulationResult:
    """Simulates `rounds` independent trials and tallies switch vs stay wins.

    Per trial, a switch wins exactly when the initial pick missed the car and
    a stay wins exactly when it didn't -- the host's reveal never changes
    which single door conceals the car, so its door-opening step doesn't
    need to be simulated here to get correct win counts.
    """
    switch_wins = 0
    stay_wins = 0
    for _ in range(rounds):
        car_door = pick_random_door()
        player_choice = pick_random_door()
        if player_choice == car_door:
            stay_wins += 1
        else:
            switch_wins += 1
    return SimulationResult(rounds=rounds, switch_wins=switch_wins, stay_wins=stay_wins)
