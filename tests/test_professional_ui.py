from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.cards import CardModel, SeriesGenerator
from app.printing import A4SvgRenderer, PrintStyle
from app.ui.main_window import BingoMainWindow
from app.ui.theme import APP_STYLESHEET


def test_modern_renderer_has_qr_zone_and_serials():
    series = SeriesGenerator(seed=7).generate("12", CardModel.A, 1)
    svg = A4SvgRenderer(style=PrintStyle(show_qr_zone=True)).render(series.cards)
    assert svg.count('class="bingo-card"') == 0
    assert svg.count('SERIAL') >= 6
    assert "ESCANEA PARA VERIFICAR" in svg
    assert "FB-BINGO" in svg


def test_operator_screen_is_connected_to_90_ball_engine():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    assert len(window._buttons) == 90
    assert window.game.current_number is None
    window.draw_number()
    assert window.game.current_number is not None
    assert window.count_label.text() == "1 de 90 bolas"
    window.toggle_pause()
    assert window.game.state.paused is True
    window.toggle_pause()
    assert window.game.state.paused is False
    window.close()
    app.processEvents()


def test_theme_contains_brand_palette():
    assert "#FF4FA3" in APP_STYLESHEET
    assert "#8FD9FF" in APP_STYLESHEET
    assert "#6C4DFF" in APP_STYLESHEET
