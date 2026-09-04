from app.cards import BulkSeriesGenerator, CardModel
from app.database import SQLiteSeriesRepository


def test_bulk_generator_creates_requested_series_and_cards(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "bulk.sqlite3")
    result = BulkSeriesGenerator(repo, seed=123).generate(quantity=10, model=CardModel.A)

    assert result.series_generated == 10
    assert result.cards_generated == 60
    assert result.first_series == 1
    assert result.last_series == 10
    assert result.first_serial == 1
    assert result.last_serial == 60
    assert repo.get("1").series_id == "1"
    assert repo.get_card("10-000010").serial == "10-000010"


def test_bulk_generator_supports_full_2500_series_range(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "bulk.sqlite3")
    result = BulkSeriesGenerator(repo, seed=7).generate(quantity=2_500, model=CardModel.B, serial_start=1)

    assert result.series_generated == 2_500
    assert result.cards_generated == 15_000
    assert result.last_series == 2_500
    assert result.last_serial == 15_000
    assert len(repo.get("2500").cards) == 6
    assert repo.get_card("2500-015000").serial == "2500-015000"
