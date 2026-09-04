from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository


def test_repository_round_trips_series_and_exact_card_matrix(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "cards.db")
    series = SeriesGenerator(seed=7).generate(12, CardModel.B, serial_start=101)

    repo.save(series)
    loaded = repo.get(12)
    loaded_card = repo.get_card("12-000101")

    assert loaded.series_id == 12
    assert loaded.cards == series.cards
    assert loaded_card == series.cards[0]


def test_repository_rejects_duplicate_series(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "cards.db")
    series = SeriesGenerator(seed=7).generate(12, CardModel.A)
    repo.save(series)

    try:
        repo.save(series)
    except ValueError as exc:
        assert "ya existe" in str(exc)
    else:
        raise AssertionError("Expected duplicate series to be rejected")
