import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main_window import BingoMainWindow


def test_manual_ball_input_registers_and_marks_board():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    assert window.game.current_number == 47
    assert window.count_label.text() == "1\nDE 90"
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
