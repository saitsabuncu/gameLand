"""Importing this package registers every Advanced-tier game.

Each import below runs that module's @register_game decorator as a side
effect, adding it to GameRegistry. These are explicit static imports
(not filesystem auto-discovery) on purpose: see games/__init__.py for why.
"""

from games.advanced import (  # noqa: F401
    chaos_game,
    game_2048,
    sudoku,
)
