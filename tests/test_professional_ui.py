from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.main import APP_STYLESHEET
from app.ui.generator_window import GeneratorWidget
from app.database.series_repository import SQLiteSeriesRepository


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
