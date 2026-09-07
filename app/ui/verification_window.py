from __future__ import annotations

from app.cards import BingoCard
from app.verification import CardCheckService, VerificationRecord, VerificationService

try:
    from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    class QWidget:  # type: ignore[no-redef]
        pass


class VerificationWindow(QWidget):
    """Verificación operativa: serial, serie, venta y premio."""

    def __init__(self, card_lookup=None, called_numbers=None, verification_service: VerificationService | None = None):
        super().__init__()
        self.card_lookup = card_lookup
        self.called_numbers = called_numbers if called_numbers is not None else set()
        self.verification_service = verification_service
        self.result: VerificationRecord | None = None
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Número del cartón")
        self.serial_input.setMaxLength(32)
        self.result_label = QLabel("Ingrese el número del cartón")
        self.detail_label = QLabel("")
        self.detail_label.setWordWrap(True)
        button = QPushButton("VERIFICAR CARTÓN")
        button.clicked.connect(self.verify)
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("VERIFICACIÓN DE CARTÓN"))
        layout.addWidget(self.serial_input)
        layout.addWidget(button)
        layout.addWidget(self.result_label)
        layout.addWidget(self.detail_label)

    def verify(self) -> VerificationRecord | None:
        serial = self.serial_input.text().strip()
        if not serial:
            self.result_label.setText("Ingrese un número de cartón")
            self.detail_label.setText("")
            return None
        try:
            if self.verification_service is not None:
                result = self.verification_service.verify(serial, set(self.called_numbers))
                self.result = result
                self._show_operational_result(result)
                return result
            if self.card_lookup is None:
                raise ValueError("No hay servicio de verificación configurado")
            card: BingoCard = self.card_lookup(serial)
        except (KeyError, LookupError, ValueError) as exc:
            self.result = None
            self.result_label.setText("✕ CARTÓN NO VÁLIDO")
            self.detail_label.setText(str(exc))
            return None

        checked = CardCheckService.check(card, set(self.called_numbers))
        self.result_label.setText(self._prize_message(checked.bingo, checked.line_rows, checked.serial))
        self.detail_label.setText(f"Modelo: {checked.model}")
        return None

    def _show_operational_result(self, result: VerificationRecord) -> None:
        self.result_label.setText(self._prize_message(result.bingo, result.line_rows, result.serial))
        sale = "NO VENDIDO" if not result.sold else f"VENDIDO · {result.seller or 'SIN VENDEDOR'}"
        if result.sale_type == "serie":
            sale += " · SERIE COMPLETA"
        self.detail_label.setText(
            f"Serie: {result.series_id} · Cartón: {result.card_index}/6\n"
            f"Estado de venta: {sale}"
        )

    @staticmethod
    def _prize_message(bingo: bool, line_rows: tuple[int, ...], serial: str) -> str:
        if bingo:
            return f"★ BINGO · CARTÓN {serial} ★"
        if line_rows:
            rows = ", ".join(str(row + 1) for row in line_rows)
            return f"✓ LÍNEA · CARTÓN {serial} · FILA(S): {rows}"
        return f"✕ SIN PREMIO · CARTÓN {serial}"
