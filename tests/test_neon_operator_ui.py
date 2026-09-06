import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import BingoMainWindow


def test_operator_window_has_approved_layout_and_90_ball_board():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    assert window.windowTitle() == "FB-BINGO — Sala de Juego"
    assert window.minimumSize().width() == 1200
    assert len(window._buttons) == 90
    assert window.current_label.objectName() == "CurrentBall"
    assert window.count_label.text() == "0\nDE 90"
    assert window.card_serial_input.placeholderText() == "Número / serial del cartón"

    window.close()
    app.processEvents()
