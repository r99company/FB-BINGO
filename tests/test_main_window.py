import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import MainWindow


def test_main_window_exposes_game_and_generator_tabs():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.tabs.count() == 2
    assert window.tabs.tabText(0) == "Sala de juego"
    assert window.tabs.tabText(1) == "Generador"

    window.close()
