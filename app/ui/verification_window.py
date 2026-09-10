from __future__ import annotations

from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer, PrintStyle
from app.verification import CardCheckService, VerificationRecord, VerificationService

try:
    from PySide6.QtCore import QByteArray, Qt
    from PySide6.QtSvgWidgets import QSvgWidget
    from PySide6.QtWidgets import QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
except ImportError:  # pragma: no cover
    class QWidget:  # type: ignore[no-redef]
        pass


class VerificationWindow(QWidget):
    """Ventana compacta de verificación que muestra el cartón con el mismo estilo de impresión."""

    def __init__(self, card_lookup=None, called_numbers=None, verification_service: VerificationService | None = None, expected_model: CardModel | str | None = None):
        super().__init__()
        self.setWindowTitle("FB-BINGO — Verificación de cartón")
        self.resize(720, 760)
        self.setMinimumSize(620, 680)
        self.card_lookup = card_lookup
        self.called_numbers = called_numbers if called_numbers is not None else set()
        self.verification_service = verification_service
        self.expected_model = expected_model
        self.result: VerificationRecord | None = None
        self.card_preview = QSvgWidget()
        self.card_preview.setMinimumHeight(390)
        self.card_preview.setProperty("svg_content", "")
        self.setStyleSheet("""
            QWidget { background:#030719; color:#F7F9FF; font-family:'Segoe UI'; }
            QLabel#Title { font-size:22px; font-weight:900; color:#FFFFFF; }
            QLabel#Model { font-size:12px; font-weight:800; color:#18D9FF; }
            QLabel#Hint { color:#AFC7E8; font-size:11px; }
            QLineEdit { background:#06142E; border:2px solid #216CA9; border-radius:8px; color:#FFFFFF; padding:10px; font-size:22px; font-weight:900; }
            QLineEdit:focus { border-color:#FF3FA4; }
            QPushButton { min-height:44px; background:#08A7D7; border:1px solid #52E6FF; border-radius:8px; color:#FFFFFF; font-weight:900; }
            QLabel#Result { font-size:19px; font-weight:900; color:#FF62B5; }
            QLabel#PrizeDetail { font-size:14px; font-weight:800; color:#DDE8FF; }
            QSvgWidget { background:#FFFFFF; border:1px solid #216CA9; border-radius:10px; }
        """)
        self.serial_input = QLineEdit(); self.serial_input.setPlaceholderText("Número del cartón"); self.serial_input.setMaxLength(32); self.serial_input.returnPressed.connect(self.verify)
        self.model_label = QLabel(self._model_text()); self.model_label.setObjectName("Model"); self.model_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_label = QLabel("Ingrese el número del cartón"); self.result_label.setObjectName("Result"); self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.detail_label = QLabel(""); self.detail_label.setObjectName("Hint"); self.detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.detail_label.setWordWrap(True)
        self.prize_detail_label = QLabel(""); self.prize_detail_label.setObjectName("PrizeDetail"); self.prize_detail_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.prize_detail_label.setWordWrap(True)
        button = QPushButton("VERIFICAR CARTÓN"); button.clicked.connect(self.verify)
        layout = QVBoxLayout(self); layout.setContentsMargins(16, 14, 16, 14); layout.setSpacing(8)
        title = QLabel("VERIFICACIÓN DE CARTÓN"); title.setObjectName("Title"); title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title); layout.addWidget(self.model_label); layout.addWidget(self.serial_input); layout.addWidget(button); layout.addWidget(self.result_label); layout.addWidget(self.card_preview, 1); layout.addWidget(self.prize_detail_label); layout.addWidget(self.detail_label)

    def set_expected_model(self, model: CardModel | str | None) -> None:
        self.expected_model = model; self.model_label.setText(self._model_text())

    def _model_text(self) -> str:
        if self.expected_model is None: return "Modelo de partida: —"
        model = self.expected_model.value if isinstance(self.expected_model, CardModel) else str(self.expected_model)
        return f"Modelo de partida: {model}"

    def _clear_card(self) -> None:
        self.card_preview.load(QByteArray()); self.card_preview.setProperty("svg_content", "")

    def _render_card(self, card: BingoCard, called_numbers: set[int] | frozenset[int]) -> None:
        renderer = A4SvgRenderer(style=PrintStyle(show_qr_zone=True, show_serial=True, show_model=False))
        svg = renderer.render_card(card, width=180.0, height=82.0)
        self.card_preview.load(QByteArray(svg.encode("utf-8"))); self.card_preview.setProperty("svg_content", svg); self.card_preview.update()

    def verify(self) -> VerificationRecord | None:
        serial = self.serial_input.text().strip()
        if not serial:
            self.result_label.setText("INGRESE EL NÚMERO DEL CARTÓN"); self.prize_detail_label.setText(""); self.detail_label.setText(""); self._clear_card(); return None
        try:
            if self.verification_service is not None:
                result = self.verification_service.verify(serial, set(self.called_numbers), expected_model=self.expected_model)
                self.result = result; self._show_operational_result(result); return result
            if self.card_lookup is None: raise ValueError("No hay servicio de verificación configurado")
            card: BingoCard = self.card_lookup(serial)
            if self.expected_model is not None and card.model.value != str(self.expected_model): raise ValueError(f"CARTÓN DE OTRO MODELO · PARTIDA: {self.expected_model} · CARTÓN: {card.model.value}")
        except (KeyError, LookupError, ValueError) as exc:
            self.result = None; self._clear_card(); self.result_label.setText("✕ CARTÓN NO VÁLIDO"); self.prize_detail_label.setText(str(exc)); self.detail_label.setText(""); return None
        checked = CardCheckService.check(card, set(self.called_numbers)); self.result_label.setText(self._prize_message(checked.bingo, checked.line_rows, checked.serial)); self.prize_detail_label.setText(self._prize_detail(checked.bingo, checked.line_rows)); self.detail_label.setText(f"Modelo: {checked.model}"); self._render_card(card, set(self.called_numbers)); return None

    def _show_operational_result(self, result: VerificationRecord) -> None:
        self.result_label.setText(self._prize_message(result.bingo, result.line_rows, result.serial)); self.prize_detail_label.setText(self._prize_detail(result.bingo, result.line_rows))
        sale = "NO VENDIDO" if not result.sold else f"VENDIDO · {result.seller or 'SIN VENDEDOR'}"
        if result.sale_type == "serie": sale += " · SERIE COMPLETA"
        self.detail_label.setText(f"Serie: {result.series_id} · Cartón: {result.card_index}/6\nModelo: {result.model.value} · Estado de venta: {sale}")
        card = self.verification_service.repository.get_card(result.serial) if self.verification_service else None
        if card is not None: self._render_card(card, set(self.called_numbers))

    @staticmethod
    def _prize_message(bingo: bool, line_rows: tuple[int, ...], serial: str) -> str:
        if bingo: return f"★ BINGO · CARTÓN {serial} ★"
        if line_rows: return f"✓ LÍNEA · CARTÓN {serial} · FILA(S): {', '.join(str(row + 1) for row in line_rows)}"
        return f"✕ NO HAY LÍNEA · NO HAY BINGO · CARTÓN {serial}"

    @staticmethod
    def _prize_detail(bingo: bool, line_rows: tuple[int, ...]) -> str:
        if bingo: return "★ BINGO · LOS 15 NÚMEROS ESTÁN JUGADOS ★"
        if line_rows: return f"✓ HAY LÍNEA · FILA(S): {', '.join(str(row + 1) for row in line_rows)}"
        return "✕ NO HAY LÍNEA · NO HAY BINGO"
