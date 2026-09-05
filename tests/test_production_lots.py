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
