import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main import MainWindow


def test_main_window_exposes_operator_generator_and_verification_tabs():
    app = QApplication.instance() or QApplication([])
    window = MainWindow()

    assert window.tabs.count() == 3
    assert [window.tabs.tabText(index) for index in range(3)] == [
        "LOCUTORA",
        "GENERADOR",
        "VERIFICACIÓN",
    ]
    window.close()
    app.processEvents()
