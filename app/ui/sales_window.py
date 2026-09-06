from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QComboBox,
    QFormLayout,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from app.sales import SalesService


SALES_QSS = """
QWidget#SalesRoot { background:#030719; color:#F7F9FF; font-family:'Segoe UI'; }
QFrame#SalesPanel { background:#07132D; border:1px solid #174A86; border-radius:12px; }
QLabel#Title { color:#18D9FF; font-size:28px; font-weight:900; }
QLabel#Caption { color:#FFFFFF; font-size:14px; font-weight:900; }
QLabel#Hint { color:#AFC7E8; font-size:11px; }
QLabel#Feedback { color:#72FF2F; font-size:14px; font-weight:900; padding:8px; }
QLineEdit,QComboBox { background:#06142E; border:1px solid #216CA9; border-radius:7px; color:#FFFFFF; padding:10px; font-size:14px; min-height:38px; }
QLineEdit:focus,QComboBox:focus { border:2px solid #FF3FA4; }
QPushButton#Register { background:#08A7D7; border:1px solid #52E6FF; border-radius:8px; color:#FFFFFF; min-height:48px; font-weight:900; }
QListWidget { background:#06142E; border:1px solid #174A86; border-radius:7px; color:#FFFFFF; padding:6px; }
"""


class SalesWindow(QMainWindow):
    """Ventana operativa para registrar cartones y series vendidos."""

    def __init__(self, database_path: str | Path) -> None:
        super().__init__()
        self.setWindowTitle("FB-BINGO — Ventas")
        self.resize(720, 620)
        self.setMinimumSize(620, 520)
        self.sales_service = SalesService(database_path)
        root = QWidget(objectName="SalesRoot")
        root.setStyleSheet(SALES_QSS)
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(18, 18, 18, 18)
        outer.setSpacing(12)

        title = QLabel("VENTAS")
        title.setObjectName("Title")
        outer.addWidget(title)
        subtitle = QLabel("Registro de cartones y series · evita ventas duplicadas")
        subtitle.setObjectName("Hint")
        outer.addWidget(subtitle)

        panel = QFrame(objectName="SalesPanel")
        form = QFormLayout(panel)
        form.setContentsMargins(18, 18, 18, 18)
        form.setSpacing(10)
        self.sale_type = QComboBox()
        self.sale_type.addItem("CARTÓN", "carton")
        self.sale_type.addItem("SERIE COMPLETA", "serie")
        self.serial_input = QLineEdit()
        self.serial_input.setPlaceholderText("Número / serial del cartón o serie")
        self.seller_input = QLineEdit()
        self.seller_input.setPlaceholderText("Nombre del vendedor")
        form.addRow("TIPO DE VENTA", self.sale_type)
        form.addRow("NÚMERO / SERIAL", self.serial_input)
        form.addRow("VENDEDOR", self.seller_input)
        outer.addWidget(panel)

        button_row = QHBoxLayout()
        button_row.addStretch()
        register = QPushButton("✓ REGISTRAR VENTA")
        register.setObjectName("Register")
        register.clicked.connect(self.register_sale)
        register.setMinimumWidth(220)
        button_row.addWidget(register)
        button_row.addStretch()
        outer.addLayout(button_row)

        self.feedback = QLabel("LISTO · ESPERANDO UNA VENTA")
        self.feedback.setObjectName("Feedback")
        self.feedback.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.feedback.setWordWrap(True)
        outer.addWidget(self.feedback)

        recent_title = QLabel("VENTAS RECIENTES")
        recent_title.setObjectName("Caption")
        outer.addWidget(recent_title)
        self.recent_sales = QListWidget()
        outer.addWidget(self.recent_sales, 1)
        self.serial_input.returnPressed.connect(self.register_sale)
        self._refresh_sales()

    def register_sale(self) -> bool:
        serial = self.serial_input.text().strip()
        sale_type = self.sale_type.currentData()
        seller = self.seller_input.text().strip()
        try:
            sale = self.sales_service.sell(serial, sale_type=sale_type, seller=seller)
        except (ValueError, TypeError) as exc:
            self.feedback.setText(f"✕ {exc}".upper())
            self.serial_input.selectAll()
            self.serial_input.setFocus()
            return False
        label = "CARTÓN" if sale.sale_type == "carton" else "SERIE"
        self.feedback.setText(f"✓ {label} {sale.serial} REGISTRADA · VENDEDOR: {sale.seller or '—'}")
        self.serial_input.clear()
        self._refresh_sales()
        self.serial_input.setFocus()
        return True

    def _refresh_sales(self) -> None:
        self.recent_sales.clear()
        for sale in self.sales_service.list_sales()[:20]:
            label = "CARTÓN" if sale.sale_type == "carton" else "SERIE"
            seller = sale.seller or "—"
            self.recent_sales.addItem(f"{sale.sold_at}  ·  {label}  ·  {sale.serial}  ·  {seller}")
