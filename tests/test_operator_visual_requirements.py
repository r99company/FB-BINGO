from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.ui.main import BingoMainWindow


def test_operator_board_uses_circular_ball_style_and_hidden_digitizer() -> None:
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    app.processEvents()

    assert len(window._buttons) == 90
    root = window.centralWidget()
    assert root is not None
    assert "border-radius:29px" in root.styleSheet()
    assert not window.ball_input.isVisible()
    assert not window.ball_message.isVisible()
    assert all(
        label.text().strip() not in {"DIGITA EL NÚMERO", "Escribe la bola física y presiona ENTER"}
        or not label.isVisible()
        for label in window.findChildren(type(window.current_label))
    )

    window.close()
    app.processEvents()
