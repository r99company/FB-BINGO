from app.cards import BingoCard, BingoSeries, CardModel
from app.database import SQLiteSeriesRepository
from app.verification import LivePrizeTracker


def _series() -> BingoSeries:
    # Serie válida de prueba: cada fila de cada cartón contiene 5 números.
    from app.cards import SeriesGenerator
    return SeriesGenerator(seed=123, max_serial=30_000).generate("0001", CardModel.A, serial_start=1)


def test_live_tracker_detects_line_and_bingo(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite")
    series = _series()
    repository.save(series)
    tracker = LivePrizeTracker(repository, max_cards=30_000)
    tracker.load()

    first = series.cards[0]
    first_row = first.row_numbers(0)
    tracker.update(first_row)
    prizes = tracker.prizes()
    matching = next(prize for prize in prizes if prize.serial == first.serial)
    assert 1 in matching.line_rows
    assert not matching.bingo

    tracker.update(first.numbers)
    matching = next(prize for prize in tracker.prizes() if prize.serial == first.serial)
    assert matching.bingo


def test_live_tracker_rewinds_when_ball_is_undone(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite")
    series = _series()
    repository.save(series)
    tracker = LivePrizeTracker(repository)
    card = series.cards[0]
    row = card.row_numbers(0)

    tracker.update(row)
    assert any(prize.serial == card.serial for prize in tracker.line_winners())
    tracker.update(row[:-1])
    assert not any(prize.serial == card.serial for prize in tracker.line_winners())
