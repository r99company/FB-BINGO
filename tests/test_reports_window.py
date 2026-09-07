from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.database.game_repository import SQLiteGameHistoryRepository
from app.ui.reports_window import ReportsWindow


def test_reports_window_lists_games_and_exports_selected(qtbot, tmp_path: Path):
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    game_id = repository.save_game(
        game_name="PARTIDA RÁPIDA",
        series_id="SERIE-001",
        called_numbers=(7, 44, 90),
        status="finalizada",
    )

    window = ReportsWindow(repository, tmp_path / "reports")
    qtbot.addWidget(window)
    window.show()

    assert window.table.rowCount() == 1
    assert window.table.item(0, 0).text() == str(game_id)
    assert window.table.item(0, 2).text() == "PARTIDA RÁPIDA"

    window.table.selectRow(0)
    output = window.export_selected()
    assert output is not None
    assert output.exists()
