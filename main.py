from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication, QMainWindow, QTabWidget

from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.generator_window import GeneratorWidget
from app.ui.main_window import BingoMainWindow
from app.ui.theme import apply_theme
from app.ui.verification_widget import VerificationWidget


def build_window() -> QMainWindow:
    window = QMainWindow()
    window.setWindowTitle("FB-BINGO · Sistema Profesional de Bingo 90")
    window.resize(1500, 930)
    tabs = QTabWidget()
    repository = SQLiteSeriesRepository(database_path())
    tabs.addTab(BingoMainWindow(), "🎙  Sala de Juego")
    tabs.addTab(GeneratorWidget(repository), "🎫  Generador de Cartones")
    tabs.addTab(VerificationWidget(repository), "✓  Verificación")
    window.setCentralWidget(tabs)
    return window


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("FB-BINGO")
    app.setOrganizationName("FB-BINGO")
    apply_theme(app)
    window = build_window()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
