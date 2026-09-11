import pytest

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.production import DuplicateProductionError, ProductionService, plan_lot


def test_1500_cards_make_250_series() -> None:
    lot = plan_lot(1, 1500)
    assert lot.card_count == 1500
    assert lot.series_count == 250


def test_lot_can_start_at_any_card_when_quantity_is_six() -> None:
    assert plan_lot(2, 7).card_count == 6
    assert plan_lot(3, 8).card_count == 6
    assert plan_lot(1501, 1506).card_count == 6

    with pytest.raises(ValueError, match="múltiplo de 6"):
        plan_lot(2, 8)


def test_official_capacity_is_30000() -> None:
    lot = plan_lot(29_995, 30_000)
    assert lot.card_count == 6
    assert lot.series_count == 1

    with pytest.raises(ValueError):
        plan_lot(30_001, 30_006)


def test_configured_capacity_must_be_positive_and_cover_requested_range() -> None:
    with pytest.raises(ValueError):
        plan_lot(1, 6, max_cards=0)
    with pytest.raises(ValueError):
        plan_lot(29_995, 30_000, max_cards=29_999)


def test_service_uses_configured_capacity(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, max_cards=30_000)
    lot = service.create_lot(29_995, 30_000, CardModel.A, operator="test")
    assert lot.start_card == 29_995
    assert lot.end_card == 30_000


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


def test_arbitrary_print_start_generates_canonical_series_then_loads_requested_six(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    lot = service.create_lot(2, 7, CardModel.A, operator="test")
    result = service.generate_lot(lot.lot_id)

    assert result.status == "generated"
    requested = repository.get_cards_range(2, 7)
    assert [int(card.serial.split("-")[-1]) for card in requested] == list(range(2, 8))
    assert repository.get_card("1").serial.endswith("000001")
    assert repository.get_card("12").serial.endswith("000012")
    assert repository.get_series_id_for_card("2") == "0001"
    assert repository.get_series_id_for_card("7") == "0002"


def test_existing_card_number_can_be_reprinted_without_duplicate_error(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)

    reprint = service.create_lot(1, 6, CardModel.A, operator="reimpresion")
    result = service.generate_lot(reprint.lot_id)

    assert result.status == "generated"
    assert repository.count_series() == 1
    assert repository.count_cards() == 6


def test_existing_arbitrary_range_can_be_reprinted_without_duplicate_error(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    generator = SeriesGenerator(seed=11)
    repository.save(generator.generate("0001", CardModel.A, serial_start=1))
    repository.save(generator.generate("0002", CardModel.A, serial_start=7))

    service = ProductionService(repository)
    lot = service.create_lot(2, 7, CardModel.A, operator="reimpresion")
    result = service.generate_lot(lot.lot_id)

    assert result.status == "generated"
    assert repository.count_cards() == 12
    assert [repository.get_card(str(n)).numbers for n in range(2, 8)]


def test_same_series_can_be_reprinted_repeatedly_with_identical_cards(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)
    original = repository.get("0001")

    for _ in range(3):
        reprint = service.create_lot(1, 6, CardModel.B, operator="reimpresion")
        service.generate_lot(reprint.lot_id)
        assert repository.get("0001") == original


def test_generation_can_resume_after_a_failure(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")

    class FailOnSecondSeries(SeriesGenerator):
        def __init__(self) -> None:
            super().__init__(seed=123)
            self.calls = 0

        def generate(self, series_id, model, serial_start=1):
            self.calls += 1
            if self.calls == 2:
                raise RuntimeError("fallo de impresión simulado")
            return super().generate(series_id, model, serial_start)

    service = ProductionService(repository, generator=FailOnSecondSeries())
    lot = service.create_lot(1, 12, CardModel.A, operator="test")

    with pytest.raises(RuntimeError, match="fallo de impresión simulado"):
        service.generate_lot(lot.lot_id)

    assert service.get_lot(lot.lot_id).status == "failed"
    assert len(repository.get("0001").cards) == 6

    resumed = ProductionService(repository, generator=SeriesGenerator(seed=456)).generate_lot(lot.lot_id)

    assert resumed.status == "generated"
    assert len(repository.get("0002").cards) == 6


def test_mismatched_persisted_series_is_not_silently_reused(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    repository.save(SeriesGenerator(seed=10).generate("0002", CardModel.A, serial_start=1))

    service = ProductionService(repository, max_cards=30_000)
    lot = service.create_lot(7, 12, CardModel.A, operator="test")

    with pytest.raises(DuplicateProductionError, match="0002"):
        service.generate_lot(lot.lot_id)

    assert service.get_lot(lot.lot_id).status == "failed"


def test_generated_lot_can_be_marked_printed_repeatedly(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    lot = service.create_lot(1, 6, CardModel.A, operator="print-test")

    with pytest.raises(ValueError, match="generado"):
        service.mark_printed(lot.lot_id)

    service.generate_lot(lot.lot_id)
    printed = service.mark_printed(lot.lot_id)
    repeated = service.mark_printed(lot.lot_id)

    assert printed.status == "printed"
    assert repeated.status == "printed"
    assert service.get_lot(lot.lot_id).status == "printed"


def test_production_keeps_new_card_layouts_unique_and_non_repetitive(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, generator=SeriesGenerator(seed=20260910))
    lot = service.create_lot(1, 600, CardModel.A, operator="uniqueness-test")
    result = service.generate_lot(lot.lot_id)

    assert result.status == "generated"
    cards = repository.get_cards_range(1, 600)
    signatures = {service._layout_signature(card) for card in cards}
    assert len(signatures) == 600

    masks = [service._layout_mask(card) for card in cards]
    for index in range(1, len(masks)):
        previous_window = masks[max(0, index - service.RECENT_LAYOUT_WINDOW):index]
        assert all(
            service._mask_distance(masks[index], previous) >= service.MIN_RECENT_LAYOUT_DISTANCE
            for previous in previous_window
        )
