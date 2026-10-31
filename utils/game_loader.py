import importlib
import pkgutil
from types import ModuleType


def discover_games(package: ModuleType) -> None:
    """Recursively imports every submodule under the given package.

    Importing a game module triggers its @register_game decorator,
    which adds the game to the GameRegistry as a side effect.
    """
    for _, module_name, is_package in pkgutil.walk_packages(
        path=package.__path__, prefix=f"{package.__name__}."
    ):
        module = importlib.import_module(module_name)
        if is_package:
            discover_games(module)
