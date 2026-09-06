from pathlib import Path

import pytest

from app.cards import BingoCard, BingoSeries, CardModel
from app.database.series_repository import SQLiteSeriesRepository
from app.sales import SalesService


def make_series() -> BingoSeries:
    grid = (
        (1, 10, 0, 30, 0, 50, 0, 70, 0),
        (0, 11, 20, 0, 40, 0, 60, 0, 80),
        (2, 0, 21, 31, 0, 51, 61, 71, 90),
    )
    cards = tuple(
        BingoCard(serial=f"C-0000{i}", model=CardModel.A, grid=grid)
        for i in range(1, 7)
    )
    return BingoSeries(series_id="S-001", cards=cards)


def test_sales_service_validates_real_card_and_series(tmp_path: Path):
    db = tmp_path / "fb-bingo.db"
    repository = SQLiteSeriesRepository(db)
    repository.save(make_series())
    service = SalesService(db, repository=repository)

    service.sell_card("C-00001", seller="Vendedor 1")
    assert service.is_card_sold("C-00001")

    with pytest.raises(ValueError, match="no existe"):
        service.sell_card("C-99999")


def test_sales_service_prevents_mixing_series_and_card_sales(tmp_path: Path):
    db = tmp_path / "fb-bingo.db"
    repository = SQLiteSeriesRepository(db)
    repository.save(make_series())
    service = SalesService(db, repository=repository)

    service.sell_series("S-001", seller="Vendedor 2")

    with pytest.raises(ValueError, match="serie ya fue vendida"):
        service.sell_card("C-00002")

    with pytest.raises(ValueError, match="cartones ya fueron vendidos"):
        service.sell_series("S-001")
