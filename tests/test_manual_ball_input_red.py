import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtWidgets import QApplication
from app.ui.main_window import BingoMainWindow

def test_manual_ball_input_contract():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    assert hasattr(window, "ball_input")
    window.ball_input.setText("47")
    window.ball_input.returnPressed.emit()
    assert window.game.current_number == 47
    assert window._buttons[46].isChecked()
    assert window.count_label.text() == "1\nDE 90"
    window.close()
    app.quit()
