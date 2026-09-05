from pathlib import Path

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.settings.paths import application_data_dir


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


def test_application_data_dir_is_not_relative_to_installation(monkeypatch, tmp_path):
    local_app_data = tmp_path / "LocalAppData"
    monkeypatch.setenv("LOCALAPPDATA", str(local_app_data))

    data_dir = application_data_dir()

    assert data_dir == local_app_data / "FB-BINGO"
    assert not str(data_dir).startswith(str(Path.cwd()))
