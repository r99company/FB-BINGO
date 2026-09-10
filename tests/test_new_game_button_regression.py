import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main import BingoMainWindow as OperationalBingoMainWindow, _f4_action


def test_f4_keyboard_action_finalizes_and_starts_a_clean_new_game():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    window.call_number(47)

    _f4_action(window)
    assert window._finalized is True

    _f4_action(window)

    assert window._finalized is False
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.count_label.text() == "0 / 90"

    window.close()
    app.quit()
