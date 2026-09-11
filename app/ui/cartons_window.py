from __future__ import annotations

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget
from PySide6.QtSvgWidgets import QSvgWidget

from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.settings.paths import database_path
from app.ui.designer_window import DesignerWindow
from app.ui.generator_window import GeneratorWidget


class CardViewer(QWidget):
    """Consulta un cartón guardado y lo muestra como cartón físico, no como tabla."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("FB-BINGO — Ver Cartones")
        self.resize(900, 620)
        self.setMinimumSize(760, 560)
        self.repo = SQLiteSeriesRepository(database_path())

        self.setStyleSheet(
            "QWidget{background:#07111F;color:#F7FAFF;font-family:'Segoe UI';}"
            "QLabel#Title{font-size:24px;font-weight:900;color:#8FD9FF;}"
            "QLabel#Info{font-size:13px;font-weight:800;color:#F49ABD;}"
            "QLabel#Status{font-size:11px;color:#A9C1D2;}"
            "QLineEdit{background:#0B1E32;border:1px solid #2B5D7D;border-radius:8px;color:#FFF;padding:9px;font-size:18px;font-weight:800;}"
            "QPushButton{background:#173D5B;border:1px solid #8FD9FF;border-radius:8px;color:#FFF;min-height:42px;padding:0 18px;font-weight:900;}"
            "QPushButton:hover{background:#20506F;}"
            "QSvgWidget{background:#FFF;border:1px solid #2D6386;border-radius:10px;}"
        )

        layout = QVBoxLayout(self)
        layout.setContentsMargins(18, 16, 18, 16)
        layout.setSpacing(10)
        title = QLabel("VER CARTÓN")
        title.setObjectName("Title")
        layout.addWidget(title)

        row = QHBoxLayout()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Número del cartón, por ejemplo 000001")
        self.input.returnPressed.connect(self.search)
        button = QPushButton("BUSCAR")
        button.clicked.connect(self.search)
        row.addWidget(self.input, 1)
        row.addWidget(button)
        layout.addLayout(row)

        self.info = QLabel("Ingrese un número y pulse BUSCAR")
        self.info.setObjectName("Info")
        self.info.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info)

        self.preview = QSvgWidget()
        self.preview.setMinimumHeight(360)
        self.preview.setVisible(False)
        layout.addWidget(self.preview, 1)

        self.status = QLabel("")
        self.status.setObjectName("Status")
        self.status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status)

    @staticmethod
    def _normalise_serial(value: str) -> str:
        value = value.strip()
        if value.isdigit():
            return str(int(value))
        return value

    def _clear_preview(self) -> None:
        self.preview.load(QByteArray())
        self.preview.setVisible(False)

    def search(self) -> None:
        serial = self._normalise_serial(self.input.text())
        if not serial:
            self.status.setText("Ingrese el número de cartón.")
            self._clear_preview()
            return

        try:
            card = self.repo.get_card(serial)
            series_id = self.repo.get_series_id_for_card(card.serial)
            renderer = A4SvgRenderer(
                style=PrintStyle(
                    show_qr_zone=True,
                    show_serial=True,
                    show_model=False,
                )
            )
            svg = renderer.render_card(card, width=190.0, height=88.0)
            self.preview.load(QByteArray(svg.encode("utf-8")))
            self.preview.setVisible(True)
            self.info.setText(
                f"CARTÓN {card.serial}   •   SERIE {series_id}   •   MODELO {card.model.value}"
            )
            self.status.setText("Cartón recuperado de la base de datos y representado con el mismo diseño de impresión.")
        except KeyError:
            self._clear_preview()
            self.info.setText("✕ CARTÓN NO ENCONTRADO")
            self.status.setText("Revise el número ingresado.")
        except Exception as exc:
            self._clear_preview()
            self.info.setText("ERROR AL CONSULTAR EL CARTÓN")
            self.status.setText(str(exc))


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
        title.setStyleSheet("font-size:28px;font-weight:900;color:#8FD9FF;")
        layout.addWidget(title)
        sub = QLabel("Seleccione la operación que desea realizar")
        sub.setStyleSheet("font-size:14px;color:#A9C1D2;")
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
