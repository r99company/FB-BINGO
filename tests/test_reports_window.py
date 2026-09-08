from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.database.game_repository import SQLiteGameHistoryRepository
from app.database.series_repository import SQLiteSeriesRepository
from app.cards import BingoCard, BingoSeries, CardModel
from app.sales import SalesService
from app.ui.reports_window import ReportsWindow


def _series() -> BingoSeries:
    # Cartón determinista y válido: 5 números por fila, 15 en total,
    # con los números dentro del rango de su columna y un máximo de 2
    # números por columna para el modelo A.
    grid = (
        (1, 10, None, None, None, 50, 60, None, 80),
        (2, None, 21, 30, None, None, None, 70, 81),
        (None, 11, None, 31, 41, None, 61, 71, None),
    )
    return BingoSeries(
        series_id=1,
        cards=tuple(
            BingoCard(serial=f"{i:06d}", model=CardModel.A, grid=grid)
            for i in range(1, 7)
        ),
    )


def test_reports_window_lists_games_and_exports_selected(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    game_id = repository.save_game(
        game_name="PARTIDA RÁPIDA",
        series_id="SERIE-001",
        called_numbers=(7, 44, 90),
        status="finalizada",
    )

    window = ReportsWindow(repository, tmp_path / "reports")
    assert window.table.rowCount() == 1
    assert window.table.item(0, 0).text() == str(game_id)
    assert window.table.item(0, 2).text() == "PARTIDA RÁPIDA"

    window.table.selectRow(0)
    output = window.export_selected()
    assert output is not None
    assert output.exists()
    window.close()
    app.processEvents()


def test_reports_window_reads_sales_from_same_database(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    db = tmp_path / "bingo.db"
    series_repository = SQLiteSeriesRepository(db)
    series_repository.save(_series())
    SalesService(db, repository=series_repository).sell_card("1", seller="Ana")

    game_repository = SQLiteGameHistoryRepository(db)
    window = ReportsWindow(game_repository, tmp_path / "reports")

    assert window.metric_total.text() == "1"
    assert window.metric_cards.text() == "1"
    assert window.metric_series.text() == "0"
    assert window.sales_table.rowCount() == 1
    assert window.sales_table.item(0, 2).text() == "000001"
    assert window.sales_table.item(0, 3).text() == "Ana"
    window.close()
    app.processEvents()


def test_reports_window_returns_none_without_selection(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    window = ReportsWindow(repository, tmp_path / "reports")
    assert window.export_selected() is None
    window.close()
    app.processEvents()
