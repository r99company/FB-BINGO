from PySide6.QtWidgets import QApplication

from app.ui.main import main
from app.ui.main_window import BingoMainWindow


def test_main_supports_test_mode(capsys):
    result = main(["--test"])
    captured = capsys.readouterr().out
    assert result == 0
    assert "FB-BINGO OK" in captured
    assert "bola_actual=None" in captured
    assert "series_en_bd=" in captured


def test_undo_preserves_pause_when_removing_last_ball():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.game.restore(window.game.state.__class__(drawn_numbers=(7,), remaining_numbers=tuple(n for n in range(1, 91) if n != 7), paused=True))
    window.undo_number()
    assert window.game.state.paused is True
    assert window.game.history == ()
    window.close()
    if app is not QApplication.instance():
        app.quit()
