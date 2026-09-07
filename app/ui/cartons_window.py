from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QPushButton, QVBoxLayout, QWidget, QMessageBox

from app.database import SQLiteSeriesRepository
from app.settings.paths import database_path
from app.ui.designer_window import DesignerWindow
from app.ui.generator_window import GeneratorWidget


class CardViewer(QWidget):
    def __init__(self):
        super().__init__(); self.setWindowTitle("FB-BINGO — Ver Cartones"); self.resize(720,520)
        self.repo=SQLiteSeriesRepository(database_path()); layout=QVBoxLayout(self)
        title=QLabel("VER CARTÓN"); title.setStyleSheet("font-size:24px;font-weight:900;"); layout.addWidget(title)
        row=QHBoxLayout(); self.input=QLineEdit(); self.input.setPlaceholderText("Número de cartón, por ejemplo 00001"); b=QPushButton("BUSCAR"); b.clicked.connect(self.search); row.addWidget(self.input); row.addWidget(b); layout.addLayout(row)
        self.result=QLabel("Ingrese un número y pulse BUSCAR"); self.result.setAlignment(Qt.AlignmentFlag.AlignCenter); self.result.setWordWrap(True); self.result.setStyleSheet("font-size:18px;font-weight:700;padding:20px;"); layout.addWidget(self.result,1)
    def search(self):
        serial=self.input.text().strip()
        if not serial:return
        try:
            card=self.repo.get_card(serial); rows=[]
            for line in card.grid: rows.append("  ".join("" if v is None else str(v) for v in line))
            self.result.setText(f"CARTÓN {card.serial}\nSERIE: {self.repo.get_series_id_for_card(card.serial)}\n\n"+"\n".join(rows))
        except KeyError:self.result.setText("✕ CARTÓN NO ENCONTRADO")


class CartonsWindow(QWidget):
    """Centro simple de Cartones: imprimir, ver y diseñar."""
    def __init__(self, parent=None):
        super().__init__(parent); self.setWindowTitle("FB-BINGO — Cartones"); self.resize(620,360); self.generator=None; self.viewer=None; self.designer=None
        layout=QVBoxLayout(self); title=QLabel("CARTONES"); title.setStyleSheet("font-size:28px;font-weight:900;color:#18D9FF;"); layout.addWidget(title); sub=QLabel("Seleccione la operación que desea realizar"); sub.setStyleSheet("font-size:14px;"); layout.addWidget(sub)
        for text,slot in (("IMPRIMIR CARTONES",self.open_generator),("VER CARTONES",self.open_viewer),("DISEÑADOR DE CARTONES",self.open_designer)):
            b=QPushButton(text); b.setMinimumHeight(64); b.setStyleSheet("font-size:16px;font-weight:900;"); b.clicked.connect(slot); layout.addWidget(b)
        layout.addStretch()
    def open_generator(self):
        if self.generator is None:self.generator=GeneratorWidget(SQLiteSeriesRepository(database_path()))
        self.generator.show(); self.generator.raise_(); self.generator.activateWindow()
    def open_viewer(self):
        if self.viewer is None:self.viewer=CardViewer()
        self.viewer.show(); self.viewer.raise_(); self.viewer.activateWindow()
    def open_designer(self):
        if self.designer is None:self.designer=DesignerWindow()
        self.designer.show(); self.designer.raise_(); self.designer.activateWindow()
