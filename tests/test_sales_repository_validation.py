from pathlib import Path

import pytest

from app.cards import CardModel, SeriesGenerator
from app.database.series_repository import SQLiteSeriesRepository
from app.sales import SalesService


def prepare_series(db: Path, series_id: str, serial_start: int):
    repository = SQLiteSeriesRepository(db)
    series = SeriesGenerator(seed=7).generate(series_id, model=CardModel.A, serial_start=serial_start)
    repository.save(series)
    return repository, series


def test_sales_service_validates_real_card_and_series(tmp_path: Path):
    db = tmp_path / "fb-bingo.db"
    repository, series = prepare_series(db, "S-001", 1)
    service = SalesService(db, repository=repository)

    service.sell_card(series.cards[0].serial, seller="Vendedor 1")
    assert service.is_card_sold(series.cards[0].serial)

    with pytest.raises(ValueError, match="no existe"):
        service.sell_card("C-99999")


def test_sales_service_prevents_mixing_series_and_card_sales(tmp_path: Path):
    db = tmp_path / "fb-bingo.db"
    repository, series = prepare_series(db, "S-001", 1)
    service = SalesService(db, repository=repository)

    service.sell_card(series.cards[0].serial, seller="Vendedor 2")

    with pytest.raises(ValueError, match="cartones ya vendidos"):
        service.sell_series(series.series_id)

    _, other = prepare_series(db, "S-002", 7)
    service.sell_series(other.series_id, seller="Vendedor 3")

    with pytest.raises(ValueError, match="ya fue vendida"):
        service.sell_card(other.cards[0].serial)
