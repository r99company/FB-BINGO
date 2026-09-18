from __future__ import annotations

from app.cards import CardModel
from app.cards.generator import SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.verification import VerificationService


def test_verification_does_not_require_a_sale_record(tmp_path) -> None:
    repo = SQLiteSeriesRepository(tmp_path / "bingo.db")
    series = SeriesGenerator(seed=91).generate("0001", CardModel.A, serial_start=13000)
    repo.save(series)
    card = repo.get_card("13000")

    result = VerificationService(repo).verify(card.serial, set(card.numbers), expected_model=CardModel.A)

    assert result.exists is True
    assert result.bingo is True
    assert result.sold is False
    assert result.series_id == "0001"
    assert result.card_index == 1


def test_verification_rejects_card_from_another_model(tmp_path) -> None:
    repo = SQLiteSeriesRepository(tmp_path / "bingo.db")
    series = SeriesGenerator(seed=92).generate("0002", CardModel.B, serial_start=14000)
    repo.save(series)
    card = repo.get_card("14000")

    try:
        VerificationService(repo).verify(card.serial, set(card.numbers), expected_model=CardModel.A)
    except ValueError as exc:
        message = str(exc)
        assert "OTRO MODELO" in message
        assert "PARTIDA: A" in message
        assert "CARTÓN: B" in message
    else:
        raise AssertionError("Se aceptó un cartón de un modelo distinto al de la partida")
