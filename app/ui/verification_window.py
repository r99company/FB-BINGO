from __future__ import annotations

from app.cards import BingoCard
from app.verification.check import CardCheckService, VerificationResult

try:
    from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    class QWidget:  # type: ignore[no-redef]
        pass


class VerificationWindow(QWidget):
    """Panel sencillo para que la locutora introduzca solo el número del cartón."""

    def __init__(self, card_lookup, called_numbers=None):
        super().__init__()
        self.card_lookup = card_lookup
        self.called_numbers = called_numbers if called_numbers is not None else set()
        self.result: VerificationResult | None = None
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Número del cartón")
        self.result_label = QLabel("Ingrese el número del cartón")
        button = QPushButton("Verificar")
        button.clicked.connect(self.verify)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("VERIFICACIÓN DE CARTÓN"))
        layout.addWidget(self.serial_input)
        layout.addWidget(button)
        layout.addWidget(self.result_label)

    def verify(self) -> VerificationResult | None:
        serial = self.serial_input.text().strip()
        if not serial:
            self.result_label.setText("Ingrese un número de cartón")
            return None
        try:
            card: BingoCard = self.card_lookup(serial)
        except (KeyError, LookupError):
            self.result_label.setText("Cartón no encontrado")
            return None
        self.result = CardCheckService.check(card, set(self.called_numbers))
        if self.result.bingo:
            message = f"BINGO · Cartón {self.result.serial} · Modelo {self.result.model}"
        elif self.result.line_rows:
            rows = ", ".join(str(row + 1) for row in self.result.line_rows)
            message = f"LÍNEA · Cartón {self.result.serial} · Fila(s): {rows}"
        else:
            message = f"SIN PREMIO · Cartón {self.result.serial}"
        self.result_label.setText(message)
        return self.result
