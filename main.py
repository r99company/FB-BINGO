from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from app.ui.generator_window import GeneratorWindow
from app.ui.main_window import BingoMainWindow


def build_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle("FB BINGO")
    window.resize(1280, 820)
    tabs = QTabWidget()
    tabs.addTab(BingoMainWindow().centralWidget(), "Sala de Juego")
    tabs.addTab(GeneratorWindow().centralWidget(), "Generador de Cartones")
    window.setCentralWidget(tabs)
    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FB BINGO")
    window = build_window()
    window.show()
    sys.exit(app.exec())
