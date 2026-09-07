from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database.game_repository import SQLiteGameHistoryRepository
from app.sales import SalesService
from app.reports.excel_exporter import export_game_history


REPORTS_QSS = """
QWidget { background:#030719; color:#F7F9FF; font-family:'Segoe UI'; }
QFrame#Card { background:#07132D; border:1px solid #174A86; border-radius:12px; }
QLabel#Title { color:#18D9FF; font-size:24px; font-weight:900; }
QLabel#MetricCaption { color:#AFC7E8; font-size:11px; font-weight:800; }
QLabel#Metric { color:#FFFFFF; font-size:25px; font-weight:900; }
QLabel#Hint { color:#AFC7E8; font-size:12px; }
QTableWidget { background:#06142E; border:1px solid #174A86; gridline-color:#174A86; }
QHeaderView::section { background:#D61A84; color:white; font-weight:900; padding:7px; }
QPushButton { background:#08A7D7; color:white; border:1px solid #52E6FF; border-radius:7px; padding:10px 16px; font-weight:900; }
"""


class ReportsWindow(QWidget):
    """Panel administrativo de partidas y ventas, con datos reales de SQLite."""

    def __init__(self, repository: SQLiteGameHistoryRepository, output_dir: str | Path) -> None:
        super().__init__()
        self.repository = repository
        self.output_dir = Path(output_dir)
        self.sales_service = SalesService(self._database_path())
        self.setWindowTitle("FB-BINGO — Reportes")
        self.resize(1080, 700)
        self.setMinimumSize(900, 620)
        self.setStyleSheet(REPORTS_QSS)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(12)
        title = QLabel("REPORTES · VENTAS Y PARTIDAS")
        title.setObjectName("Title")
        layout.addWidget(title)
        hint = QLabel("Este panel muestra inmediatamente las ventas registradas y el historial de partidas. Use ACTUALIZAR después de registrar operaciones.")
        hint.setObjectName("Hint")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        metrics = QGridLayout()
        metrics.setSpacing(10)
        self.metric_total = self._metric(metrics, 0, 0, "VENTAS TOTALES")
        self.metric_cards = self._metric(metrics, 0, 1, "CARTONES VENDIDOS")
        self.metric_series = self._metric(metrics, 0, 2, "SERIES VENDIDAS")
        self.metric_games = self._metric(metrics, 0, 3, "PARTIDAS REGISTRADAS")
        layout.addLayout(metrics)

        sales_title = QLabel("VENTAS REGISTRADAS")
        sales_title.setObjectName("Metric")
        sales_title.setText("VENTAS REGISTRADAS")
        sales_title.setStyleSheet("font-size:16px;color:#18D9FF;")
        layout.addWidget(sales_title)
        self.sales_table = QTableWidget(0, 4)
        self.sales_table.setHorizontalHeaderLabels(["Fecha", "Tipo", "Número / Serie", "Vendedor"])
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.sales_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.sales_table, 1)

        games_title = QLabel("HISTORIAL DE PARTIDAS")
        games_title.setObjectName("Metric")
        games_title.setText("HISTORIAL DE PARTIDAS")
        games_title.setStyleSheet("font-size:16px;color:#18D9FF;")
        layout.addWidget(games_title)
        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["ID", "Fecha", "Juego", "Serie", "Bolas", "Estado"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.table, 1)

        actions = QHBoxLayout()
        actions.addStretch()
        refresh = QPushButton("ACTUALIZAR")
        refresh.clicked.connect(self.refresh)
        actions.addWidget(refresh)
        self.export_button = QPushButton("EXPORTAR EXCEL")
        self.export_button.clicked.connect(self.export_selected)
        actions.addWidget(self.export_button)
        layout.addLayout(actions)
        self.refresh()

    def _database_path(self) -> Path:
        # Both game history and sales must point to the exact same SQLite file.
        # SQLiteGameHistoryRepository stores it as ``path``; using output_dir
        # here could silently create a second empty database and make Reports
        # appear to show no sales.
        return Path(self.repository.path)

    @staticmethod
    def _metric(grid: QGridLayout, row: int, column: int, caption: str) -> QLabel:
        card = QFrame(objectName="Card")
        box = QVBoxLayout(card)
        small = QLabel(caption)
        small.setObjectName("MetricCaption")
        value = QLabel("0")
        value.setObjectName("Metric")
        box.addWidget(small)
        box.addWidget(value)
        grid.addWidget(card, row, column)
        return value

    def refresh(self) -> None:
        summary = self.sales_service.summary()
        self.metric_total.setText(f"{summary.total:,}")
        self.metric_cards.setText(f"{summary.cards:,}")
        self.metric_series.setText(f"{summary.series:,}")

        games = self.repository.list_games()
        self.metric_games.setText(f"{len(games):,}")
        self.table.setRowCount(len(games))
        for row_index, game in enumerate(games):
            values = (
                str(game["game_id"]),
                str(game["finished_at"] or game["created_at"]),
                str(game["game_name"]),
                str(game["series_id"]),
                str(len(game["called_numbers"])),
                str(game["status"]),
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_index, column, item)

        sales = self.sales_service.list_sales()
        self.sales_table.setRowCount(len(sales))
        for row_index, sale in enumerate(sales):
            values = (
                sale.sold_at,
                "CARTÓN" if sale.sale_type == "carton" else "SERIE COMPLETA",
                sale.serial,
                sale.seller or "SIN VENDEDOR",
            )
            for column, value in enumerate(values):
                item = QTableWidgetItem(value)
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sales_table.setItem(row_index, column, item)

    def export_selected(self) -> Path | None:
        row = self.table.currentRow()
        if row < 0:
            return None
        game_id = int(self.table.item(row, 0).text())
        game = self.repository.get_game(game_id)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        output = self.output_dir / f"FB-BINGO-partida-{game_id}-reporte.xlsx"
        return export_game_history(
            output,
            game_name=game["game_name"],
            series=game["series_id"],
            called_numbers=game["called_numbers"],
            finished_at=game["finished_at"] or game["created_at"],
            status=game["status"],
        )
