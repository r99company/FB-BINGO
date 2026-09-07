from pathlib import Path

import pytest

from app.cards import CardModel, SeriesGenerator
from app.database.series_repository import SQLiteSeriesRepository
from app.sales import SalesService
from app.verification.service import VerificationService


def prepare(tmp_path: Path):
    db = tmp_path / "fb-bingo.db"
    repository = SQLiteSeriesRepository(db)
    series = SeriesGenerator(seed=22).generate("S-001", CardModel.A, 100)
    repository.save(series)
    sales = SalesService(db, repository=repository)
    return repository, series, sales


def test_verification_returns_card_series_position_and_sale(tmp_path: Path):
    repository, series, sales = prepare(tmp_path)
    card = series.cards[2]
    sales.sell_card(card.serial, seller="Vendedor Norte")

    result = VerificationService(repository, sales).verify(card.serial, set(card.numbers))

    assert result.exists is True
    assert result.serial == card.serial
    assert result.series_id == series.series_id
    assert result.card_index == 3
    assert result.sold is True
    assert result.seller == "Vendedor Norte"
    assert result.bingo is True


def test_verification_finds_existing_but_unsold_card(tmp_path: Path):
    repository, series, sales = prepare(tmp_path)
    card = series.cards[0]

    result = VerificationService(repository, sales).verify(card.serial, set(card.numbers))

    assert result.exists is True
    assert result.sold is False
    assert result.seller == ""
    assert result.has_prize is True


def test_verification_rejects_unknown_serial(tmp_path: Path):
    repository, _, sales = prepare(tmp_path)

    with pytest.raises(ValueError, match="no existe"):
        VerificationService(repository, sales).verify("999999", {1, 2, 3})


def test_verification_rejects_invalid_called_number(tmp_path: Path):
    repository, series, sales = prepare(tmp_path)

    with pytest.raises(ValueError, match="1 y 90"):
        VerificationService(repository, sales).verify(series.cards[0].serial, {91})
