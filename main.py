import sys

from PyQt6.QtWidgets import QApplication

import games  # noqa: F401  -- import alone registers every game, see games/__init__.py
from ui.main_window import MainWindow


def main() -> None:
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
