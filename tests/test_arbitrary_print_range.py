import pytest

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.production import ProductionService, plan_lot


def test_plan_lot_accepts_any_start_and_exact_card_quantity() -> None:
    lot = plan_lot(2, 7)
    assert lot.start_card == 2
    assert lot.end_card == 7
    assert lot.card_count == 6
    assert lot.series_count == 1


def test_plan_lot_accepts_1501_as_start() -> None:
    lot = plan_lot(1501, 1506)
    assert lot.start_card == 1501
    assert lot.end_card == 1506


def test_existing_generated_cards_are_loaded_for_reprint_without_error(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    generator = SeriesGenerator(seed=11)
    repository.save(generator.generate("0001", CardModel.A, serial_start=1))
    repository.save(generator.generate("0002", CardModel.A, serial_start=7))

    service = ProductionService(repository)
    lot = service.create_lot(2, 7, CardModel.A, operator="reimpresion")
    result = service.generate_lot(lot.lot_id)

    assert result.status == "generated"
    assert repository.count_cards() == 12


def test_printing_same_range_repeatedly_is_allowed(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A)
    service.generate_lot(first.lot_id)

    for _ in range(5):
        repeat = service.create_lot(1, 6, CardModel.A)
        assert service.generate_lot(repeat.lot_id).status == "generated"


def test_starting_at_three_is_not_rejected_as_non_series_boundary() -> None:
    lot = plan_lot(3, 8)
    assert lot.card_count == 6
