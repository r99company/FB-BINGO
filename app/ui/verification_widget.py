from __future__ import annotations

from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QVBoxLayout, QWidget
from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.verification.verifier import CardVerifier


class VerificationWidget(QWidget):
    """Verificación rápida por serial usando el cartón almacenado."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(database_path())
        self.called: set[int] = set()
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        row = QHBoxLayout()
        self.serial = QLineEdit()
        self.serial.setPlaceholderText("Ej. 1-000001")
        self.serial.returnPressed.connect(self.verify)
        button = QPushButton("VERIFICAR")
        button.clicked.connect(self.verify)
        row.addWidget(self.serial); row.addWidget(button)
        root.addLayout(row)
        self.called_input = QLineEdit()
        self.called_input.setPlaceholderText("Números llamados, separados por coma")
        root.addWidget(self.called_input)
        self.result = QLabel("Ingrese un serial y los números llamados.")
        self.result.setWordWrap(True)
        root.addWidget(self.result)

    def verify(self) -> None:
        try:
            card = self.repository.get_card(self.serial.text().strip())
            called = {int(value.strip()) for value in self.called_input.text().split(",") if value.strip()}
            verifier = CardVerifier(card)
            lines = verifier.line_winners(called)
            bingo = verifier.is_bingo(called)
            model = card.model.value
            status = f"Modelo {model} · Serial {card.serial}\n"
            status += f"Línea: {', '.join(str(row + 1) for row in lines) if lines else 'NO'}\n"
            status += f"BINGO: {'SÍ' if bingo else 'NO'}"
            self.result.setText(status)
        except (KeyError, ValueError) as exc:
            QMessageBox.warning(self, "Verificación", str(exc))
