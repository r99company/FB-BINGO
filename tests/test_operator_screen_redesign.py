from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtGui import QKeySequence
from PySide6.QtWidgets import QApplication, QLineEdit

from app.cards import CardModel, SeriesGenerator
from app.ui.main_window import BingoMainWindow
from app.ui.verification_window import VerificationWindow


def test_operator_screen_has_board_left_and_clean_input_only():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()

    assert len(window._buttons) == 90
    assert window.ball_input.placeholderText() == "1–90"
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


def test_ctrl5_is_dedicated_verification_shortcut():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    sequences = [shortcut.key().toString(QKeySequence.SequenceFormat.NativeText) for shortcut in window._operator_shortcuts]
    assert any("Ctrl+5" in value for value in sequences)
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
