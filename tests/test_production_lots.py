import pytest

from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.production import DuplicateProductionError, ProductionService, plan_lot


def test_1500_cards_make_250_series() -> None:
    lot = plan_lot(1, 1500)
    assert lot.card_count == 1500
    assert lot.series_count == 250


def test_lot_must_use_complete_six_card_series() -> None:
    with pytest.raises(ValueError, match="límites completos"):
        plan_lot(1, 1499)


def test_generation_persists_series_and_reports_progress(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, generator=None)
    lot = service.create_lot(1, 6, CardModel.A, operator="test")
    progress: list[int] = []

    result = service.generate_lot(lot.lot_id, progress.append)

    assert result.status == "generated"
    assert progress == [6]
    stored = repository.get("0001")
    assert len(stored.cards) == 6
    assert sorted(n for card in stored.cards for n in card.numbers) == list(range(1, 91))


def test_existing_card_number_cannot_be_generated_again(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)

    with pytest.raises(DuplicateProductionError):
        service.create_lot(1, 6, CardModel.A, operator="test")
