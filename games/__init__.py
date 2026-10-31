"""Importing `games` registers every game in GameRegistry.

Previously this registration was driven by utils.game_loader.discover_games(),
which walked the filesystem (pkgutil.walk_packages) to find and import every
game module dynamically. That broke completely under PyInstaller: a frozen
build's pure-Python packages live only inside a zipped archive, not as loose
files on disk, so `games.__path__` pointed at a directory pkgutil could not
see into -- the packaged app silently launched with ZERO games and no error
anywhere (confirmed by building and running it). Filesystem walking and a
frozen build are fundamentally incompatible, so dynamic discovery was
dropped rather than patched around.

These are now plain, explicit static imports instead: each tier subpackage
(games.beginner, games.intermediate, games.advanced) imports its own game
modules, and this file imports the three tiers. A static `import games`
(already done once, in main.py) is then enough to register everything --
in a normal run and in a PyInstaller build alike, since PyInstaller's
static analysis follows ordinary import statements correctly. Adding a new
game now means adding one import line to its tier's __init__.py, a small,
explicit, visible cost in exchange for working at all once packaged.
"""

from games import advanced, beginner, intermediate  # noqa: F401
