from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.production import ProductionService
from app.ui.generator_window import GeneratorWidget


def test_generator_exposes_model_a_and_model_b(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository)

    assert [widget.model.itemData(i) for i in range(widget.model.count())] == ["A", "B"]
    assert widget.model.itemText(0).startswith("Modelo A")
    assert widget.model.itemText(1).startswith("Modelo B")

    widget.close()
    app.processEvents()


def test_model_b_generation_persists_real_model_b_cards(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    lot = service.create_lot(7, 12, CardModel.B, operator="test-model-b")
    result = service.generate_lot(lot.lot_id)

    assert result.model is CardModel.B
    series = repository.get("0002")
    assert len(series.cards) == 6
    assert all(card.model is CardModel.B for card in series.cards)
