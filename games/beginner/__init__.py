"""Importing this package registers every Beginner-tier game.

Each import below runs that module's @register_game decorator as a side
effect, adding it to GameRegistry. These are explicit static imports
(not filesystem auto-discovery) on purpose: see games/__init__.py for why.
"""

from games.beginner import (  # noqa: F401
    hangman,
    math_quiz,
    number_guessing,
    prime_number_hunter,
)
