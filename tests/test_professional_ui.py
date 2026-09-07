from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import ProductionService
from app.ui.generator_window import GeneratorWidget
from app.ui.main_window import BingoMainWindow
from app.ui.theme import APP_STYLESHEET


def test_modern_renderer_has_qr_zone_and_serials():
    series = SeriesGenerator(seed=7).generate("12", CardModel.A, 1)
    svg = A4SvgRenderer(style=PrintStyle(show_qr_zone=True)).render(series.cards)
    assert svg.count('class="bingo-card"') == 6
    assert svg.count("SERIAL") >= 6
    assert svg.count('class="qr-zone"') == 6
    assert "ESCANEA PARA VERIFICAR" in svg
    assert "FB-BINGO" in svg


def test_modern_renderer_can_print_without_qr_zone():
    series = SeriesGenerator(seed=8).generate("13", CardModel.A, 7)
    svg = A4SvgRenderer(style=PrintStyle(show_qr_zone=False)).render(series.cards)
    assert svg.count('class="bingo-card"') == 6
    assert svg.count("SERIAL") >= 6
    assert 'class="qr-zone"' not in svg
    assert "ESCANEA PARA VERIFICAR" not in svg


def test_operator_screen_is_connected_to_90_ball_engine():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    assert len(window._buttons) == 90
    assert window.game.current_number is None
    window.draw_number()
    assert window.game.current_number is not None
    assert window.count_label.text() == "1\nDE 90"
    window.toggle_pause()
    assert window.game.state.paused is True
    window.toggle_pause()
    assert window.game.state.paused is False
    window.close()
    app.processEvents()


def test_generator_navigation_opens_generator_window():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    generator_buttons = [
        b for b in window.findChildren(type(window.pause_button))
        if "GENERADOR" in b.text().upper()
    ]
    assert len(generator_buttons) == 1
    assert window.generator_window is None
    generator_buttons[0].click()
    assert window.generator_window is not None
    assert window.generator_window.isVisible()
    window.generator_window.close()
    window.close()
    app.processEvents()


def test_generator_uses_production_service_for_persistent_generation(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository)

    assert isinstance(widget.production_service, ProductionService)
    lot = widget.production_service.create_lot(1, 6, CardModel.A, operator="ui-test")
    result = widget.production_service.generate_lot(lot.lot_id)

    assert result.status == "generated"
    assert repository.get("0001").cards[0].serial.endswith("000001")
    widget.close()
    app.processEvents()


def test_generator_can_be_configured_for_30000_cards(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository, max_cards=30_000)

    assert widget.production_service.max_cards == 30_000
    assert widget.series_id.maximum() == 5_000
    assert widget.serial_start.maximum() == 29_995

    widget.series_id.setValue(5_000)
    assert widget.serial_start.value() == 29_995

    widget.serial_start.setValue(29_995)
    assert widget.series_id.value() == 5_000
    widget.close()
    app.processEvents()


def test_theme_contains_brand_palette():
    assert "#FF4FA3" in APP_STYLESHEET
    assert "#8FD9FF" in APP_STYLESHEET
    assert "#6C4DFF" in APP_STYLESHEET
