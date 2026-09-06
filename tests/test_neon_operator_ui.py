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
    assert window.ball_input.placeholderText() == "Digite la bola (1-90)"
    assert window.ball_input.hasFocus()

    window.close()
    app.processEvents()


def test_manual_ball_entry_updates_board_and_rejects_duplicates_and_invalid_values():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    window.ball_input.setText("47")
    assert window.enter_ball() is True
    assert window.game.history == (47,)
    assert window.current_label.text() == "47"
    assert window.count_label.text() == "1\nDE 90"
    assert window._buttons[47].property("called") is True
    assert window._buttons[47].property("current") is True

    window.ball_input.setText("47")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.ball_input.setText("91")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.ball_input.setText("0")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.ball_input.setText("abc")
    assert window.enter_ball() is False
    assert window.game.history == (47,)

    window.close()
    app.processEvents()
