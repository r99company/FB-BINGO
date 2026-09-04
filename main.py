from __future__ import annotations

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget
from app.database import SQLiteSeriesRepository
from app.ui.generator_window import GeneratorWidget
from app.ui.main_window import BingoMainWindow
from app.ui.verification_widget import VerificationWidget


def build_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle("FB BINGO")
    window.resize(1280, 820)
    tabs = QTabWidget()
    repository = SQLiteSeriesRepository("data/fb_bingo.db")
    tabs.addTab(BingoMainWindow(), "Sala de Juego")
    tabs.addTab(GeneratorWidget(repository), "Generador de Cartones")
    tabs.addTab(VerificationWidget(repository), "Verificación")
    window.setCentralWidget(tabs)
    return window


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setApplicationName("FB BINGO")
    window = build_window()
    window.show()
    sys.exit(app.exec())
