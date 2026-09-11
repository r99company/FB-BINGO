import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main import BingoMainWindow


def _close(window) -> None:
    window.close()
    app = QApplication.instance()
    if app is not None:
        app.processEvents()


def test_operator_board_uses_circular_90_ball_controls_and_hides_digitizer():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    assert len(window._buttons) == 90
    assert all(button.width() == 58 and button.height() == 58 for button in window._buttons.values())
    assert window.ball_input.isHidden()
    assert window.ball_message.isHidden()
    assert window.minimumWidth() >= 1200
    assert window.minimumHeight() >= 760
    _close(window)
    app.quit()
