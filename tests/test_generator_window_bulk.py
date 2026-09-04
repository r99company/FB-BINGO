from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.ui.generator_window import BulkGenerationWorker


def test_bulk_worker_reports_progress_and_result(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "bulk.sqlite3")
    worker = BulkGenerationWorker(repo, start_series=1, quantity=3, model=CardModel.A, serial_start=1, seed=123)

    progress = []
    results = []
    errors = []
    worker.progress.connect(lambda current, total, cards: progress.append((current, total, cards)))
    worker.finished.connect(results.append)
    worker.error.connect(errors.append)

    worker.run()

    assert errors == []
    assert progress[-1] == (3, 3, 18)
    assert results[0].series_generated == 3
    assert results[0].cards_generated == 18
    assert repo.get("3").series_id == "3"
