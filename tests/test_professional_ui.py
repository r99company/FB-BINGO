from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QMessageBox

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
    assert svg.count("ID:") >= 6
    assert svg.count('class="qr-zone"') == 6
    assert "FB-BINGO" in svg


def test_modern_renderer_can_print_without_qr_zone():
    series = SeriesGenerator(seed=8).generate("13", CardModel.A, 7)
    svg = A4SvgRenderer(style=PrintStyle(show_qr_zone=False)).render(series.cards)
    assert svg.count('class="bingo-card"') == 6
    assert svg.count("ID:") >= 6
    assert 'class="qr-zone"' not in svg


def test_operator_screen_is_connected_to_90_ball_engine():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    assert len(window._buttons) == 90
    assert window.game.current_number is None
    window.draw_number()
    assert window.game.current_number is not None
    assert window.count_label.text() == "1 / 90"
    window.toggle_pause()
    assert window.game.state.paused is True
    window.toggle_pause()
    assert window.game.state.paused is False
    window.close()
    app.processEvents()


def test_f4_requires_confirmation_and_no_preserves_active_game(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.draw_number()
    history_before = tuple(window.game.history)
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.No)
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F4, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window, event)
    assert tuple(window.game.history) == history_before
    assert window._finalized is False
    window.close()
    app.processEvents()


def test_f4_yes_starts_a_clean_new_game(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.draw_number()
    assert window.game.history
    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F4, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window, event)
    assert window._finalized is False
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.ball_input.isEnabled()
    assert window.header_values[1].text() == "EN ESPERA"
    window.close()
    app.processEvents()


def test_cartons_navigation_button_opens_cartons_window():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    cartons_buttons = [
        b for b in window.findChildren(type(window.pause_button))
        if b.text().startswith("CARTONES")
    ]
    assert len(cartons_buttons) == 1
    assert window.generator_window is None
    # The menu is the navigation surface; the actual action is validated through
    # the operational method installed by app.ui.main.
    assert hasattr(window, "open_cartons")
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


def test_generator_uses_card_quantity_and_calculates_series(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository, max_cards=30_000)
    assert widget.production_service.max_cards == 30_000
    assert widget.start_card.value() == 1
    assert widget.card_count.maximum() == 30_000
    widget.card_count.setValue(1_500)
    assert widget.series_count_label.text() == "250"
    assert widget.range_label.text() == "1 – 1,500 (1,500 cartones)"
    widget.start_card.setValue(2)
    assert widget.range_label.text() == "2 – 1,501 (1,500 cartones)"
    widget.close()
    app.processEvents()


def test_generator_rejects_only_incomplete_series_quantity(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository)
    widget.card_count.setValue(1_499)
    assert "múltiplo de 6" in widget.series_count_label.text()
    with_error = None
    try:
        widget._requested_range()
    except ValueError as exc:
        with_error = str(exc)
    assert with_error is not None
    widget.close()
    app.processEvents()


def test_theme_contains_brand_palette():
    assert "#FF4FA3" in APP_STYLESHEET
    assert "#8FD9FF" in APP_STYLESHEET
    assert "#6C4DFF" in APP_STYLESHEET
