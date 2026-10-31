"""Importing this package registers every Intermediate-tier game.

Each import below runs that module's @register_game decorator as a side
effect, adding it to GameRegistry. These are explicit static imports
(not filesystem auto-discovery) on purpose: see games/__init__.py for why.
"""

from games.intermediate import (  # noqa: F401
    math_countdown,
    monty_hall,
    nim_game,
)
