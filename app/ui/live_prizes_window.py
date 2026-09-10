from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

from app.verification.live_prizes import LivePrize, LivePrizeTracker


class LivePrizesWindow(QDialog):
    """Panel privado del operador: premios que ya están disponibles en la partida."""

    def __init__(self, tracker: LivePrizeTracker, parent=None) -> None:
        super().__init__(parent)
        self.tracker = tracker
        self.setWindowTitle("FB-BINGO · Premios en juego")
        self.resize(720, 560)
        self.setModal(False)
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        title = QLabel("PREMIOS EN JUEGO")
        title.setStyleSheet("font-size:24px;font-weight:900;")
        root.addWidget(title)
        self.summary = QLabel("Sin bolas cantadas")
        self.summary.setStyleSheet("font-size:14px;font-weight:700;")
        root.addWidget(self.summary)

        self.list = QListWidget()
        self.list.setAlternatingRowColors(True)
        root.addWidget(self.list, 1)

        close = QPushButton("CERRAR")
        close.clicked.connect(self.close)
        row = QHBoxLayout(); row.addStretch(); row.addWidget(close)
        root.addLayout(row)

    def refresh(self, called_numbers: set[int] | frozenset[int]) -> None:
        self.tracker.update(called_numbers)
        prizes = self.tracker.prizes()
        lines = [prize for prize in prizes if not prize.bingo]
        bingos = [prize for prize in prizes if prize.bingo]
        self.summary.setText(
            f"{self.tracker.called_count} bolas cantadas · "
            f"{len(lines)} cartones con línea · {len(bingos)} con BINGO"
        )
        self.list.clear()
        for prize in prizes:
            row_text = self._format_prize(prize)
            item = QListWidgetItem(row_text)
            item.setData(Qt.ItemDataRole.UserRole, prize.serial)
            self.list.addItem(item)
        if not prizes:
            self.list.addItem("Todavía no hay cartones con línea o BINGO.")

    @staticmethod
    def _format_prize(prize: LivePrize) -> str:
        if prize.bingo:
            return f"★ BINGO  ·  CARTÓN {prize.serial}  ·  SERIE {prize.series_id}  ·  POSICIÓN {prize.card_index}/6"
        rows = ", ".join(str(row) for row in prize.line_rows)
        return f"✓ LÍNEA {rows}  ·  CARTÓN {prize.serial}  ·  SERIE {prize.series_id}  ·  POSICIÓN {prize.card_index}/6"
