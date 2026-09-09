import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import BingoMainWindow


def test_current_ball_and_called_status_have_clear_vertical_separation():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.show()
    app.processEvents()

    gap = window.call_state.geometry().top() - window.current_label.geometry().bottom()

    assert gap >= 8
    window.close()
