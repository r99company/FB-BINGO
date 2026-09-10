import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QPushButton

from app.ui.main import BingoMainWindow as OperationalBingoMainWindow


def test_finalize_button_becomes_new_game_and_starts_new_game_when_clicked():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    window.call_number(47)

    finish_button = next(
        button for button in window.findChildren(QPushButton)
        if button.property("fb_bingo_finish_button") is True
    )

    window.finalize_game()
    assert "NUEVA PARTIDA" in finish_button.text()
    assert window._finalized is True

    finish_button.click()

    assert window._finalized is False
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.count_label.text() == "0 / 90"
    assert "FINALIZAR" in finish_button.text()

    window.close()
    app.quit()
