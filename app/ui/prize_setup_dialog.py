from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox, QDialog, QFrame, QHBoxLayout, QLabel, QPushButton,
    QVBoxLayout, QWidget,
)

PRIZE_QSS = """
QDialog, QWidget#PrizeRoot { background:#030814; color:#F7FAFF; font-family:'Segoe UI'; }
QFrame#PrizeCard { background:#091A2D; border:1px solid #1D5A80; border-radius:14px; }
QLabel#Title { color:#00D9FF; font-size:25px; font-weight:900; }
QLabel#Subtitle { color:#8FD9FF; font-size:11px; }
QLabel#PrizeName { color:#FFFFFF; font-size:16px; font-weight:900; }
QLabel#PrizeDescription { color:#A9CBE0; font-size:11px; }
QCheckBox { color:#FFFFFF; font-size:12px; font-weight:800; spacing:8px; }
QCheckBox::indicator { width:22px; height:22px; }
QCheckBox::indicator:unchecked { background:#04152C; border:1px solid #5085A4; border-radius:6px; }
QCheckBox::indicator:checked { background:#0878BE; border:2px solid #00D9FF; border-radius:6px; }
QPushButton { min-height:42px; border-radius:8px; padding:0 18px; font-weight:900; color:#FFFFFF; background:#06152B; border:1px solid #0878BE; }
QPushButton#Primary { background:#0878BE; border:2px solid #00D9FF; }
QPushButton#Primary:hover { background:#0A91D2; }
QPushButton:hover { border-color:#FF49B5; }
"""


class PrizeSetupDialog(QDialog):
    """Configura los premios que regirán una partida antes de iniciar el sorteo."""

    def __init__(self, prizes: dict[str, bool] | None = None, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("FB-BINGO · Preparar partida")
        self.setMinimumWidth(560)
        self.setStyleSheet(PRIZE_QSS)
        values = {"line": True, "double_line": True, "missing_one": True, "bingo": True, "second_bingo": False}
        if prizes:
            values.update(prizes)

        root = QWidget(objectName="PrizeRoot")
        self.setLayout(QVBoxLayout())
        self.layout().setContentsMargins(22, 20, 22, 20)
        self.layout().setSpacing(12)
        self.layout().addWidget(root)
        body = QVBoxLayout(root)
        body.setContentsMargins(0, 0, 0, 0)
        body.setSpacing(12)

        title = QLabel("PREPARAR PARTIDA")
        title.setObjectName("Title")
        body.addWidget(title)
        subtitle = QLabel("Selecciona los premios válidos para esta partida. Puedes cambiar la selección antes de iniciar.")
        subtitle.setObjectName("Subtitle")
        subtitle.setWordWrap(True)
        body.addWidget(subtitle)

        self.checkboxes: dict[str, QCheckBox] = {}
        options = [
            ("line", "LÍNEA", "Completar una fila horizontal del cartón."),
            ("double_line", "DOBLE LÍNEA", "Completar dos filas horizontales del mismo cartón."),
            ("missing_one", "FALTA UNO", "Queda un número para completar el bingo."),
            ("bingo", "BINGO", "Completar los 15 números del cartón."),
            ("second_bingo", "SEGUNDO BINGO", "Después del primer bingo, continuar la partida hasta completar otro cartón. Opcional."),
        ]
        for key, name, description in options:
            card = QFrame()
            card.setObjectName("PrizeCard")
            row = QHBoxLayout(card)
            row.setContentsMargins(15, 12, 15, 12)
            labels = QVBoxLayout()
            labels.setSpacing(4)
            heading = QLabel(name)
            heading.setObjectName("PrizeName")
            detail = QLabel(description)
            detail.setObjectName("PrizeDescription")
            detail.setWordWrap(True)
            labels.addWidget(heading)
            labels.addWidget(detail)
            row.addLayout(labels, 1)
            check = QCheckBox("ACTIVO")
            check.setChecked(values[key])
            self.checkboxes[key] = check
            row.addWidget(check, 0, Qt.AlignmentFlag.AlignVCenter)
            body.addWidget(card)

        note = QLabel("Las reglas seleccionadas se aplican a la comprobación de cartones de esta partida.")
        note.setObjectName("Subtitle")
        note.setWordWrap(True)
        body.addWidget(note)

        buttons = QHBoxLayout()
        buttons.addStretch()
        cancel = QPushButton("CANCELAR")
        cancel.clicked.connect(self.reject)
        buttons.addWidget(cancel)
        start = QPushButton("INICIAR PARTIDA")
        start.setObjectName("Primary")
        start.clicked.connect(self.accept)
        buttons.addWidget(start)
        body.addLayout(buttons)

    def selected_prizes(self) -> dict[str, bool]:
        return {key: box.isChecked() for key, box in self.checkboxes.items()}
