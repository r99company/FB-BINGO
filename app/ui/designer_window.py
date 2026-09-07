from __future__ import annotations

import json
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont
from PySide6.QtWidgets import (
    QComboBox, QDoubleSpinBox, QFileDialog, QFormLayout, QFrame,
    QGridLayout, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton,
    QSpinBox, QVBoxLayout, QWidget,
)

from app.settings.paths import application_data_dir


class DesignerWindow(QWidget):
    """Diseñador persistente de modelos de cartón."""
    def __init__(self):
        super().__init__()
        self.setWindowTitle("FB-BINGO — Diseñador de Cartones")
        self.resize(1180, 760)
        self.setMinimumSize(980, 650)
        self.path = application_data_dir() / "card_designs.json"
        self.designs = self._load()
        self._build()
        self._load_design(self.model.currentText())

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) and data else self._defaults()
        except (OSError, ValueError):
            return self._defaults()

    @staticmethod
    def _defaults():
        return {"Neutral": {"width_cm": 12.0, "height_cm": 9.0, "font": "Segoe UI", "font_size": 18, "title": "Bingo", "logo": "", "bg": "#FFFFFF", "empty": "#F2E9FF", "accent": "#FF4FA3", "border": "#1453B8", "show_serial": True}}

    def _build(self):
        self.setStyleSheet("QWidget{background:#030719;color:white;font-family:'Segoe UI';} QFrame{background:#07132D;border:1px solid #174A86;border-radius:10px;} QLineEdit,QComboBox,QSpinBox,QDoubleSpinBox{background:#06142E;color:white;border:1px solid #216CA9;padding:7px;border-radius:6px;} QPushButton{background:#1453B8;color:white;border:1px solid #38A9FF;padding:9px;border-radius:7px;font-weight:800;} QLabel#Title{font-size:24px;font-weight:900;color:#18D9FF;}")
        outer = QVBoxLayout(self)
        title = QLabel("DISEÑADOR DE CARTONES"); title.setObjectName("Title"); outer.addWidget(title)
        body = QHBoxLayout()
        controls = QFrame(); form = QFormLayout(controls)
        self.model = QComboBox(); self.model.addItems(list(self.designs.keys())); self.model.currentTextChanged.connect(self._load_design); form.addRow("DISEÑO", self.model)
        nr = QHBoxLayout(); self.new_name = QLineEdit(); self.new_name.setPlaceholderText("Nombre del nuevo diseño"); b = QPushButton("NUEVO"); b.clicked.connect(self._new); nr.addWidget(self.new_name); nr.addWidget(b); form.addRow("NUEVO DISEÑO", nr)
        self.font = QComboBox(); self.font.addItems(["Segoe UI", "Arial", "Calibri", "Tahoma", "Verdana", "Times New Roman", "DejaVu Sans"]); self.font.currentTextChanged.connect(self._preview); form.addRow("TIPO DE LETRA", self.font)
        self.font_size = QSpinBox(); self.font_size.setRange(6, 72); self.font_size.valueChanged.connect(self._preview); form.addRow("TAMAÑO LETRA", self.font_size)
        self.width = QDoubleSpinBox(); self.width.setRange(5, 30); self.width.setDecimals(1); self.width.setSuffix(" cm"); self.width.valueChanged.connect(self._preview); form.addRow("ANCHO CARTÓN", self.width)
        self.height = QDoubleSpinBox(); self.height.setRange(4, 25); self.height.setDecimals(1); self.height.setSuffix(" cm"); self.height.valueChanged.connect(self._preview); form.addRow("ALTO CARTÓN", self.height)
        self.title_text = QLineEdit(); self.title_text.textChanged.connect(self._preview); form.addRow("TEXTO SUPERIOR", self.title_text)
        self.logo = QLineEdit(); self.logo.setReadOnly(True); lb = QPushButton("SELECCIONAR LOGO"); lb.clicked.connect(self._logo); lr = QHBoxLayout(); lr.addWidget(self.logo); lr.addWidget(lb); form.addRow("LOGO", lr)
        self.bg, self.empty, self.accent, self.border = (QLineEdit() for _ in range(4))
        for label, widget in (("FONDO", self.bg), ("ESPACIOS VACÍOS", self.empty), ("COLOR PRINCIPAL", self.accent), ("COLOR BORDES", self.border)):
            widget.textChanged.connect(self._preview); form.addRow(label, widget)
        self.serial = QComboBox(); self.serial.addItem("Mostrar", True); self.serial.addItem("Ocultar", False); self.serial.currentIndexChanged.connect(self._preview); form.addRow("NÚMERO CARTÓN", self.serial)
        actions = QHBoxLayout(); save = QPushButton("GUARDAR"); save.clicked.connect(self._save); delete = QPushButton("ELIMINAR"); delete.clicked.connect(self._delete); actions.addWidget(save); actions.addWidget(delete); form.addRow(actions)
        body.addWidget(controls, 1)
        preview = QFrame(); pl = QVBoxLayout(preview); cap = QLabel("VISTA PREVIA"); cap.setAlignment(Qt.AlignmentFlag.AlignCenter); pl.addWidget(cap)
        self.card = QFrame(); self.card.setFixedSize(600, 450); cl = QVBoxLayout(self.card); self.pt = QLabel("Bingo"); self.pt.setAlignment(Qt.AlignmentFlag.AlignCenter); cl.addWidget(self.pt)
        grid = QGridLayout(); self.cells = []; values = [[1,None,22,34,None,57,None,79,None],[6,None,27,None,None,59,67,None,83],[None,13,30,49,None,62,78,None,None]]
        for r in range(3):
            for c in range(9):
                x = QLabel("" if values[r][c] is None else str(values[r][c])); x.setAlignment(Qt.AlignmentFlag.AlignCenter); self.cells.append(x); grid.addWidget(x, r, c)
        cl.addLayout(grid, 1); self.serial_preview = QLabel("00001"); self.serial_preview.setAlignment(Qt.AlignmentFlag.AlignRight); cl.addWidget(self.serial_preview); pl.addWidget(self.card, 1, Qt.AlignmentFlag.AlignCenter); body.addWidget(preview, 2); outer.addLayout(body, 1)

    def _load_design(self, name):
        if name not in self.designs: return
        d = self.designs[name]; self.font.setCurrentText(d.get("font", "Segoe UI")); self.font_size.setValue(int(d.get("font_size", 18))); self.width.setValue(float(d.get("width_cm", 12))); self.height.setValue(float(d.get("height_cm", 9))); self.title_text.setText(d.get("title", "Bingo")); self.logo.setText(d.get("logo", "")); self.bg.setText(d.get("bg", "#FFFFFF")); self.empty.setText(d.get("empty", "#F2E9FF")); self.accent.setText(d.get("accent", "#FF4FA3")); self.border.setText(d.get("border", "#1453B8")); self.serial.setCurrentIndex(0 if d.get("show_serial", True) else 1); self._preview()

    def _preview(self, *_):
        self.card.setStyleSheet(f"background:{self.bg.text()};border:3px solid {self.border.text()};border-radius:12px;")
        self.pt.setText(self.title_text.text()); self.pt.setFont(QFont(self.font.currentText(), self.font_size.value(), QFont.Weight.Bold)); self.pt.setStyleSheet(f"color:{self.accent.text()};")
        for x in self.cells: x.setStyleSheet(f"border:1px solid {self.border.text()};padding:7px;background:{self.empty.text() if not x.text() else self.bg.text()};color:#111;font-size:{max(8,self.font_size.value()-2)}px;")
        self.serial_preview.setVisible(bool(self.serial.currentData()))

    def _new(self):
        name = self.new_name.text().strip()
        if not name or name in self.designs: return
        self.designs[name] = dict(self.designs["Neutral"]); self.model.addItem(name); self.model.setCurrentText(name); self.new_name.clear()

    def _logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg *.svg)")
        if path: self.logo.setText(path); self._preview()

    def _save(self):
        name = self.model.currentText()
        self.designs[name] = {"width_cm": self.width.value(), "height_cm": self.height.value(), "font": self.font.currentText(), "font_size": self.font_size.value(), "title": self.title_text.text(), "logo": self.logo.text(), "bg": self.bg.text(), "empty": self.empty.text(), "accent": self.accent.text(), "border": self.border.text(), "show_serial": bool(self.serial.currentData())}
        self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps(self.designs, ensure_ascii=False, indent=2), encoding="utf-8"); QMessageBox.information(self, "Diseño guardado", f"'{name}' quedó guardado.")

    def _delete(self):
        name = self.model.currentText()
        if name == "Neutral" or name not in self.designs: return
        self.designs.pop(name); self.model.removeItem(self.model.currentIndex()); self.path.parent.mkdir(parents=True, exist_ok=True); self.path.write_text(json.dumps(self.designs, ensure_ascii=False, indent=2), encoding="utf-8")
