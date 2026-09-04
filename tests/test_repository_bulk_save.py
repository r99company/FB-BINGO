from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository


def test_repository_save_many_persists_all_series_atomically(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "bulk.sqlite3")
    generator = SeriesGenerator(seed=5)
    series = [generator.generate(str(i), CardModel.A, serial_start=(i - 1) * 6 + 1) for i in range(1, 4)]

    repo.save_many(series)

    assert repo.get("1").cards[0].serial == "1-000001"
    assert repo.get("3").cards[-1].serial == "3-000018"
