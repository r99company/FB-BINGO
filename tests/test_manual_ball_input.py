import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import BingoMainWindow
from app.ui.main import BingoMainWindow as OperationalBingoMainWindow


def test_manual_ball_input_registers_and_marks_board():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    assert window.game.current_number == 47
    assert window.count_label.text() == "1 / 90"
    assert window._buttons[47].property("called") is True
    assert window._buttons[47].property("current") is True
    assert window.ball_input.text() == ""
    window.close()
    app.quit()


def test_manual_ball_input_rejects_duplicate_and_out_of_range():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    assert len(window.game.history) == 1
    window.ball_input.setText("91")
    window.ball_input.returnPressed.emit()
    assert len(window.game.history) == 1
    window.close()
    app.quit()


def test_operational_board_click_does_not_register_while_paused():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    window.toggle_pause()
    window.call_number(47)
    assert window.game.history == ()
    window.close()
    app.quit()


def test_undo_preserves_paused_state():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    window.call_number(47)
    window.toggle_pause()
    assert window.game.state.paused is True
    window.undo_number()
    assert window.game.history == ()
    assert window.game.state.paused is True
    window.close()
    app.quit()


def test_finalize_keeps_history_and_blocks_more_balls():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    window.finalize_game()
    assert window.game.history == (47,)
    assert window.game.current_number == 47
    assert window.game.state.finished is False
    window.ball_input.setText("12")
    window.ball_input.returnPressed.emit()
    assert window.game.history == (47,)
    assert "FINALIZADA" in window.ball_message.text()
    window.close()
    app.quit()


def test_new_game_clears_previous_game():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    window.finalize_game()
    window.new_game()
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.game.state.finished is False
    assert window.count_label.text() == "0 / 90"
    window.close()
    app.quit()


def test_verify_card_uses_current_game_history():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    assert hasattr(window, "verify_card")
    assert window.game.history == ()
    window.close()
    app.quit()
