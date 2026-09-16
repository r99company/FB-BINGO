from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication, QFrame, QLabel, QPushButton

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import ProductionService
from app.ui.generator_window import GeneratorWidget
from app.ui.main_window import BingoMainWindow
from app.ui.main_window import PROFESSIONAL_QSS
from app.ui.theme import APP_STYLESHEET
from app.ui.main import BingoMainWindow as OperationalBingoMainWindow, _f4_action


def test_same_series_id_is_deterministic():
    first = SeriesGenerator(seed=123).generate("0001", CardModel.A, 1)
    second = SeriesGenerator(seed=123).generate("0001", CardModel.A, 1)
    third = SeriesGenerator(seed=123).generate("0002", CardModel.A, 7)
    assert [card.grid for card in first.cards] == [card.grid for card in second.cards]
    assert [card.grid for card in first.cards] != [card.grid for card in third.cards]


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
    window.toggle_pause(); assert window.game.state.paused is True
    window.toggle_pause(); assert window.game.state.paused is False
    window.close(); app.processEvents()


def test_f4_finishes_active_game():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow(); window.draw_number()
    assert window.game.history
    _f4_action(window)
    assert window._finalized is True
    assert window.header_values[1].text() == "FINALIZADA"
    window.close(); app.processEvents()


def test_f4_starts_a_clean_new_game_after_finalization():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow(); window.draw_number(); _f4_action(window)
    _f4_action(window)
    assert window._finalized is False
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.ball_input.isEnabled()
    assert window.header_values[1].text() == "EN ESPERA"
    window.close(); app.processEvents()


def test_cartons_navigation_button_opens_cartons_window():
    app = QApplication.instance() or QApplication([])
    window = OperationalBingoMainWindow()
    buttons = [b for b in window.findChildren(type(window.pause_button)) if b.text().startswith("CARTONES")]
    assert len(buttons) == 1
    assert hasattr(window, "open_cartons")
    window.close(); app.processEvents()


def test_generator_uses_series_quantity_and_calculates_cartons(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository, max_cards=30_000)
    assert widget.production_service.max_cards == 30_000
    assert widget.start_card.value() == 1
    assert widget.series_count.value() == 1
    widget.series_count.setValue(250)
    assert widget.cards_label.text() == "1,500 (250 series × 6)"
    assert widget.range_label.text() == "1 – 1,500"
    widget.start_card.setValue(1_501)
    assert widget.range_label.text() == "1,501 – 3,000"
    widget.close(); app.processEvents()


def test_generator_accepts_only_first_card_of_a_series(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository)
    widget.start_card.setValue(8)
    assert widget.start_card.value() == 7
    widget.close(); app.processEvents()


def test_generator_same_range_is_idempotent_not_reprint(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository)
    widget.series_count.setValue(2)
    widget.generate_series()
    first = [card.grid for card in repository.get_cards_range(1, 12)]
    widget.generate_series()
    second = [card.grid for card in repository.get_cards_range(1, 12)]
    assert first == second
    assert widget.generate_button.text() == "CARGAR / GENERAR SERIES"
    widget.close(); app.processEvents()


def test_theme_contains_brand_palette():
    assert "#FF4FA3" in APP_STYLESHEET
    assert "#8FD9FF" in APP_STYLESHEET
    assert "#6C4DFF" in APP_STYLESHEET


def test_operator_visual_style_is_clean_and_brand_consistent():
    assert "font-family:'Segoe UI'" in PROFESSIONAL_QSS
    assert "border-radius:14px" in PROFESSIONAL_QSS
    assert "#8FD9FF" in PROFESSIONAL_QSS
    assert "#F49ABD" in PROFESSIONAL_QSS
    assert "QPushButton#Ball[current=\"true\"]" in PROFESSIONAL_QSS
    assert "QPushButton#Ball[called=\"true\"]" in PROFESSIONAL_QSS
    assert "QLineEdit#BallInput" in PROFESSIONAL_QSS


def test_operator_visual_hierarchy_uses_roomier_cards_and_controls():
    assert "QFrame#Panel { background:#0D2036; border-color:#245679; border-radius:16px; }" in PROFESSIONAL_QSS
    assert "QPushButton#Secondary { min-height:42px;" in PROFESSIONAL_QSS
    assert "QPushButton#Ball { min-width:46px; min-height:46px;" in PROFESSIONAL_QSS
    assert "QLabel#CurrentBall { color:#FFFFFF; font-size:90px;" in PROFESSIONAL_QSS


def test_operator_screen_uses_circular_neon_balls_and_no_footer_controls():
    assert "QPushButton#Ball { min-width:64px; min-height:64px;" in PROFESSIONAL_QSS
    assert "border-radius:32px" in PROFESSIONAL_QSS
    assert "QPushButton#Ball[called=\"true\"]" in PROFESSIONAL_QSS
    assert "QPushButton#Ball[current=\"true\"]" in PROFESSIONAL_QSS
    assert "QFrame#BottomBar" not in PROFESSIONAL_QSS


def test_operator_header_contains_navigation_and_small_clock():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    top_buttons = [button.text() for button in window.findChildren(QPushButton)]
    assert any("CONTROLES DE SALA" in text for text in top_buttons)
    assert any("CARTONES" in text for text in top_buttons)
    assert any("AYUDA" in text for text in top_buttons)
    assert window.findChild(QLabel, "ClockLabel") is not None
    assert window.findChild(QFrame, "BottomBar") is None
    window.close(); app.processEvents()


def test_current_ball_is_bigger_and_circular():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    assert window.current_label.width() >= 220
    assert window.current_label.height() >= 220
    assert "border-radius:120px" in PROFESSIONAL_QSS
    window.close(); app.processEvents()
