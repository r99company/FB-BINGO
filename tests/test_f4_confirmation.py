from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

import app.ui.main as operational_main
from app.ui.main import BingoMainWindow, _f4_action


def test_f4_new_game_can_be_cancelled_without_erasing_state(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.draw_number()
    _f4_action(window)
    assert window._finalized is True

    monkeypatch.setattr(operational_main, "_confirm_new_game", lambda _window: False)
    window.show()
    _f4_action(window)

    assert window._finalized is True
    assert window.game.history
    assert window.ball_message.text() == "NUEVA PARTIDA CANCELADA · SE CONSERVA EL ESTADO"
    window.close()
    app.processEvents()
