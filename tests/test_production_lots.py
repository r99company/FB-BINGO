import pytest

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.production import DuplicateProductionError, ProductionService, plan_lot


def test_1500_cards_make_250_series() -> None:
    lot = plan_lot(1, 1500)
    assert lot.card_count == 1500
    assert lot.series_count == 250


def test_lot_must_use_complete_six_card_series() -> None:
    with pytest.raises(ValueError, match="límites completos"):
        plan_lot(1, 1499)


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

    assert service.get_lot(lot.lot_id).status == "generating"
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

    assert service.get_lot(lot.lot_id).status == "generating"


def test_generated_lot_can_be_marked_printed_and_cannot_be_reprinted(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    lot = service.create_lot(1, 6, CardModel.A, operator="print-test")

    with pytest.raises(ValueError, match="generado"):
        service.mark_printed(lot.lot_id)

    service.generate_lot(lot.lot_id)
    printed = service.mark_printed(lot.lot_id)

    assert printed.status == "printed"
    assert service.get_lot(lot.lot_id).status == "printed"

    with pytest.raises(DuplicateProductionError, match="ya fue marcado como impreso"):
        service.mark_printed(lot.lot_id)
