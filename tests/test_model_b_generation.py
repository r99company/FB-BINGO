from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.production import DuplicateProductionError, ProductionService
from app.ui.generator_window import GeneratorWidget


def test_generator_exposes_model_a_and_model_b(tmp_path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    widget = GeneratorWidget(repository)

    assert [widget.model.itemData(i) for i in range(widget.model.count())] == ["A", "B"]
    assert widget.model.currentData() == "A"

    widget.close()
    app.processEvents()


def test_model_b_generation_persists_model_b_cards(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    lot = service.create_lot(7, 12, CardModel.B, operator="test-model-b")
    result = service.generate_lot(lot.lot_id)

    assert result.model is CardModel.B
    series = repository.get("0002")
    assert all(card.model is CardModel.B for card in series.cards)
    assert all(card.serial.endswith(f"{number:06d}") for card, number in zip(series.cards, range(7, 13)))


def test_model_b_does_not_silently_reuse_model_a_cards(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    lot_a = service.create_lot(1, 6, CardModel.A, operator="test-model-a")
    service.generate_lot(lot_a.lot_id)

    lot_b = service.create_lot(1, 6, CardModel.B, operator="test-model-b")

    with pytest.raises(DuplicateProductionError, match="Modelo B.*Modelo A|Modelo A.*Modelo B"):
        service.generate_lot(lot_b.lot_id)
