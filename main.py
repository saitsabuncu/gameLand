import sys

from PyQt6.QtWidgets import QApplication

import games
from ui.main_window import MainWindow
from utils.game_loader import discover_games


def main() -> None:
    discover_games(games)

    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
