import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import BingoMainWindow


def test_manual_ball_input_does_not_change_game_while_paused():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.toggle_pause()
    window.ball_input.setText("47")
    result = window.enter_ball()
    assert result is False
    assert window.game.history == ()
    assert window.game.state.paused is True
    window.close()
    app.quit()
