from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main import BingoMainWindow, _f4_action


def _window():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.show()
    app.processEvents()
    return app, window


def test_game_lifecycle_finalize_then_confirmed_new_game_resets_everything(monkeypatch):
    app, window = _window()
    window.call_number(12)
    window.call_number(34)
    assert window.game.history == (12, 34)

    _f4_action(window)
    assert window._finalized is True
    assert window.game.history == (12, 34)
    assert window.ball_input.isEnabled() is False

    monkeypatch.setattr("app.ui.main._confirm_new_game", lambda _window: True)
    _f4_action(window)

    assert window._finalized is False
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.game.state.paused is False
    assert window.ball_input.isEnabled() is True
    assert window.header_values[1].text() == "EN ESPERA"
    window.close()
    app.processEvents()


def test_pause_and_resume_preserve_called_balls():
    app, window = _window()
    window.call_number(8)
    window.toggle_pause()
    assert window.game.state.paused is True
    assert window.game.history == (8,)

    window.toggle_pause()
    assert window.game.state.paused is False
    assert window.game.history == (8,)
    window.close()
    app.processEvents()


def test_undo_removes_last_ball():
    app, window = _window()
    window.call_number(11)
    window.call_number(22)
    window.undo_number()
    assert window.game.history == (11,)
    assert window.game.current_number == 11
    window.close()
    app.processEvents()
