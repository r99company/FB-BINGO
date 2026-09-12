import pytest

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.production import ProductionService, plan_lot


def test_plan_lot_still_accepts_arbitrary_ranges_for_printing_metadata() -> None:
    lot = plan_lot(2, 7)
    assert lot.start_card == 2
    assert lot.end_card == 7
    assert lot.card_count == 6


def test_existing_cards_can_be_loaded_for_printing_from_any_card_number(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    generator = SeriesGenerator(seed=11)
    repository.save(generator.generate("0001", CardModel.A, serial_start=1))
    repository.save(generator.generate("0002", CardModel.A, serial_start=7))

    cards = repository.get_cards_range(2, 7)

    assert [card.serial for card in cards] == [
        "0001-000002", "0001-000003", "0001-000004",
        "0001-000005", "0001-000006", "0002-000007",
    ]
    assert len(cards) == 6


def test_generation_service_rejects_a_range_that_crosses_series_boundary(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    with pytest.raises(ValueError, match="múltiplo de 6|serie"):
        service.create_lot(2, 7, CardModel.A, operator="generador")


def test_generation_service_keeps_global_series_boundaries(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    first = service.create_lot(1, 6, CardModel.A)
    second = service.create_lot(7, 12, CardModel.A)

    assert (first.start_card, first.end_card) == (1, 6)
    assert (second.start_card, second.end_card) == (7, 12)


def test_printing_same_existing_range_does_not_create_new_cards(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    generator = SeriesGenerator(seed=11)
    repository.save(generator.generate("0001", CardModel.A, serial_start=1))
    repository.save(generator.generate("0002", CardModel.A, serial_start=7))
    before = repository.count_cards()

    cards = repository.get_cards_range(2, 7)

    assert len(cards) == 6
    assert repository.count_cards() == before
