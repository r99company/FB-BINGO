import pytest

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository


def test_save_and_load_preserves_series_exactly(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    series = SeriesGenerator(seed=123).generate("SER-001", CardModel.B, serial_start=100)

    repository.save(series)
    loaded = repository.get("SER-001")

    assert loaded.series_id == series.series_id
    assert loaded.cards == series.cards
    assert all(card.model is CardModel.B for card in loaded.cards)


def test_repository_rejects_duplicate_series(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    series = SeriesGenerator(seed=1).generate("SER-001", CardModel.A)
    repository.save(series)

    with pytest.raises(ValueError, match="ya existe"):
        repository.save(series)


def test_repository_lookup_by_card_serial(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    series = SeriesGenerator(seed=2).generate("SER-002", CardModel.B, serial_start=500)
    repository.save(series)

    card = repository.get_card("SER-002-000503")

    assert card.serial == "SER-002-000503"
    assert card.model is CardModel.B
    assert card == series.cards[3]
