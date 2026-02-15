"""Factum — Анализ паспортов оборудования.

Точка входа приложения.
"""

import sys
import logging
from pathlib import Path

# Добавить корень проекта в PYTHONPATH
sys.path.insert(0, str(Path(__file__).parent))

from PyQt6.QtWidgets import QApplication
from gui.main_window import MainWindow

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Factum")
    app.setOrganizationName("Factum")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
