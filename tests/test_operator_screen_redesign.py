from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QLineEdit, QPushButton

from app.cards import CardModel, SeriesGenerator
from app.ui.main_window import BingoMainWindow
from app.ui.verification_window import VerificationWindow


def test_operator_screen_has_board_left_and_clean_input_only():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    assert len(window._buttons) == 90
    placeholder = window.ball_input.placeholderText().replace(" ", "")
    assert placeholder in {"1–90", "1-90", "1�90"}
    assert not hasattr(window, "finish_button")
    assert window.findChildren(QLineEdit) and window.ball_input in window.findChildren(QLineEdit)

    window.close()
    app.processEvents()


def test_operator_screen_uses_circular_recent_ball_indicators():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    history_balls = getattr(window, "history_balls")

    assert len(history_balls) == 5
    assert all(ball.objectName() == "HistoryBall" for ball in history_balls)
    assert all(ball.property("history_index") is not None for ball in history_balls)

    window.close()
    app.processEvents()


def test_help_menu_documents_ctrl5_verifier_shortcut():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    menu_buttons = [button for button in window.findChildren(QPushButton) if button.text().startswith("AYUDA")]
    assert len(menu_buttons) == 1
    assert any("Ctrl+5" in action.text() and "Verificador" in action.text() for action in menu_buttons[0].menu().actions())
    window.close()
    app.processEvents()


def test_verification_window_renders_the_real_card_style():
    app = QApplication.instance() or QApplication([])
    card = SeriesGenerator(seed=41).generate("0001", CardModel.B, 1).cards[0]
    window = VerificationWindow(called_numbers={1, 2, 3})

    window._render_card(card, {1, 2, 3})

    svg = window.card_preview.property("svg_content")
    assert isinstance(svg, str)
    assert 'class="bingo-card"' in svg
    assert str(card.serial.split("-")[-1]) in svg
    assert "FB-BINGO" in svg

    window.close()
    app.processEvents()
