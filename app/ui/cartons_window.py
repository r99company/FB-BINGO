from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.designer_window import DesignerWindow
from app.ui.generator_window import GeneratorWidget


class CardViewer(QWidget):
    """Consulta un cartón guardado y muestra su matriz real, sin regenerarla."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FB-BINGO — Ver Cartones")
        self.resize(760, 620)
        self.repo = SQLiteSeriesRepository(database_path())

        layout = QVBoxLayout(self)
        title = QLabel("VER CARTÓN")
        title.setStyleSheet("font-size:24px;font-weight:900;")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Número de cartón, por ejemplo 000001")
        self.input.returnPressed.connect(self.search)
        button = QPushButton("BUSCAR")
        button.clicked.connect(self.search)
        row.addWidget(self.input, 1)
        row.addWidget(button)
        layout.addLayout(row)

        self.info = QLabel("Ingrese un número y pulse BUSCAR")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.info.setStyleSheet("font-size:17px;font-weight:700;padding:8px;")
        layout.addWidget(self.info)

        self.table = QTableWidget(3, 9)
        self.table.setHorizontalHeaderLabels([str(i) for i in range(1, 10)])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self.table.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.table.setMinimumHeight(300)
        self.table.setStyleSheet(
            "QTableWidget{font-size:24px;font-weight:900;gridline-color:#888;}"
            "QHeaderView::section{font-size:14px;font-weight:900;padding:5px;}"
        )
        for col in range(9):
            self.table.setColumnWidth(col, 72)
        for row_index in range(3):
            self.table.setRowHeight(row_index, 72)
        layout.addWidget(self.table)

        self.status = QLabel("")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.status.setStyleSheet("font-size:14px;font-weight:700;padding:8px;")
        layout.addWidget(self.status)

    @staticmethod
    def _normalise_serial(value: str) -> str:
        value = value.strip()
        if not value:
            return value
        if value.isdigit():
            return str(int(value))
        return value

    def _clear_table(self) -> None:
        for r in range(3):
            for c in range(9):
                self.table.setItem(r, c, QTableWidgetItem(""))

    def search(self) -> None:
        serial = self._normalise_serial(self.input.text())
        if not serial:
            self.status.setText("Ingrese el número de cartón.")
            return

        try:
            card = self.repo.get_card(serial)
            series_id = self.repo.get_series_id_for_card(card.serial)
        except KeyError:
            self._clear_table()
            self.info.setText("✕ CARTÓN NO ENCONTRADO")
            self.status.setText("Revise el número ingresado.")
            return
        except Exception as exc:
            self._clear_table()
            self.info.setText("ERROR AL CONSULTAR EL CARTÓN")
            self.status.setText(str(exc))
            return

        self.info.setText(f"CARTÓN {card.serial}    •    SERIE {series_id}    •    MODELO {card.model.value}")
        self.status.setText("Cartón recuperado directamente de la base de datos.")

        for r, line in enumerate(card.grid):
            for c, value in enumerate(line):
                item = QTableWidgetItem("" if value is None else str(value))
                item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                item.setFont(QFont("Arial", 24, QFont.Weight.Bold))
                self.table.setItem(r, c, item)


class CartonsWindow(QWidget):
    """Centro de Cartones: imprimir, ver y diseñar."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FB-BINGO — Cartones")
        self.resize(620, 360)
        self.generator = None
        self.viewer = None
        self.designer = None

        layout = QVBoxLayout(self)
        title = QLabel("CARTONES")
        title.setStyleSheet("font-size:28px;font-weight:900;color:#18D9FF;")
        layout.addWidget(title)
        sub = QLabel("Seleccione la operación que desea realizar")
        sub.setStyleSheet("font-size:14px;")
        layout.addWidget(sub)

        for text, slot in (
            ("IMPRIMIR CARTONES", self.open_generator),
            ("VER CARTONES", self.open_viewer),
            ("DISEÑADOR DE CARTONES", self.open_designer),
        ):
            button = QPushButton(text)
            button.setMinimumHeight(64)
            button.setStyleSheet("font-size:16px;font-weight:900;")
            button.clicked.connect(slot)
            layout.addWidget(button)
        layout.addStretch()

    def open_generator(self):
        if self.generator is None:
            self.generator = GeneratorWidget(SQLiteSeriesRepository(database_path()))
        self.generator.show()
        self.generator.raise_()
        self.generator.activateWindow()

    def open_viewer(self):
        if self.viewer is None:
            self.viewer = CardViewer()
        self.viewer.show()
        self.viewer.raise_()
        self.viewer.activateWindow()

    def open_designer(self):
        if self.designer is None:
            self.designer = DesignerWindow()
        self.designer.show()
        self.designer.raise_()
        self.designer.activateWindow()
