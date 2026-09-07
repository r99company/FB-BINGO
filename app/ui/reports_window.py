from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.game_repository import SQLiteGameHistoryRepository
from app.reports.excel_exporter import export_game_history


class ReportsWindow(QWidget):
    """Historial de partidas y exportación Excel para administración."""

    def __init__(self, repository: SQLiteGameHistoryRepository, output_dir: str | Path) -> None:
        super().__init__()
        self.repository = repository
        self.output_dir = Path(output_dir)
        self.setWindowTitle("FB-BINGO — Reportes")
        self.resize(980, 560)
        self.setStyleSheet(
            "QWidget{background:#030719;color:#F7F9FF;font-family:'Segoe UI';}"
            "QLabel#Title{font-size:22px;font-weight:900;color:#18D9FF;}"
            "QTableWidget{background:#07132D;border:1px solid #174A86;gridline-color:#174A86;}"
            "QHeaderView::section{background:#D61A84;color:white;font-weight:900;padding:7px;}"
            "QPushButton{background:#08A7D7;color:white;border:1px solid #52E6FF;"
            "border-radius:7px;padding:10px 16px;font-weight:900;}"
        )
        layout = QVBoxLayout(self)
        title = QLabel("REPORTES · HISTORIAL DE PARTIDAS")
        title.setObjectName("Title")
        layout.addWidget(title)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Fecha", "Juego", "Serie", "Bolas", "Estado"]
        )
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)
        actions = QHBoxLayout()
        actions.addStretch()
        self.export_button = QPushButton("EXPORTAR EXCEL")
        self.export_button.clicked.connect(self.export_selected)
        actions.addWidget(self.export_button)
        layout.addLayout(actions)
        self.refresh()

    def refresh(self) -> None:
        games = self.repository.list_games()
        self.table.setRowCount(len(games))
        for row_index, game in enumerate(games):
            values = (
                str(game["game_id"]),
                str(game["finished_at"] or game["created_at"]),
                game["game_name"],
                game["series_id"],
                str(len(game["called_numbers"])),
                game["status"],
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, column, item)

    def export_selected(self) -> Path | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        game_id = int(self.table.item(row, 0).text())
        game = self.repository.get_game(game_id)
        output = self.output_dir / f"FB-BINGO-partida-{game_id}-reporte.xlsx"
        return export_game_history(
            output,
            game_name=game["game_name"],
            series=game["series_id"],
            called_numbers=game["called_numbers"],
            finished_at=game["finished_at"] or game["created_at"],
            status=game["status"],
        )
