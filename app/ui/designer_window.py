from __future__ import annotations

import json
from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox, QColorDialog, QComboBox, QFileDialog, QFrame, QHBoxLayout,
    QLabel, QLineEdit, QListWidget, QListWidgetItem, QMessageBox, QPushButton,
    QSpinBox, QStackedWidget, QVBoxLayout, QWidget,
)

from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer, PrintStyle
from app.settings.paths import application_data_dir

SECTIONS = ("General", "Colores", "Logo", "Numeración", "QR y Seguridad", "Texto inferior", "Tamaño", "Vista previa")


class DesignerWindow(QWidget):
    designChanged = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FB-BINGO — Diseñador Profesional de Cartones")
        self.resize(1480, 900)
        self.setMinimumSize(1180, 760)
        self.path = application_data_dir() / "card_designs.json"
        self.designs = self._load()
        self._preview_card_number = "11534"
        self._build()
        self._load_design(self.model.currentText())
        self.section_list.setCurrentRow(0)

    def _defaults(self):
        return {"FB-BINGO Profesional": {
            "font": "Arial", "font_size": 18, "width_mm": 120, "height_mm": 77,
            "title": "FB-BINGO", "tagline": "¡LA DIVERSIÓN QUE NOS UNE!",
            "footer": "BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA", "logo": "",
            "bg": "#FFFFFF", "empty": "#F7DDE7", "accent": "#FF4FA3",
            "secondary_accent": "#8FD9FF", "border": "#8FD9FF", "number": "#171B2B",
            "show_serial": True, "show_qr": True, "show_model": False,
            "show_footer": True, "show_tagline": True,
        }}

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            base = self._defaults()["FB-BINGO Profesional"]
            if isinstance(data, dict) and data:
                return {k: {**base, **v} for k, v in data.items() if isinstance(v, dict)}
        except (OSError, ValueError, TypeError):
            pass
        return self._defaults()

    def _persist(self):
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.designs, ensure_ascii=False, indent=2), encoding="utf-8")

    def _build(self):
        self.setStyleSheet("QWidget{background:#F4F7FC;color:#17213A;font-family:'Segoe UI';}QFrame#Sidebar{background:#0C1730;border:0;border-radius:16px;}QFrame#Panel{background:#FFF;border:1px solid #DCE4F0;border-radius:16px;}QLabel#Brand{color:#FFF;font-size:20px;font-weight:900;padding:6px 8px;}QLabel#SubBrand,QLabel#Muted{color:#71819A;font-size:11px;}QLabel#PageTitle{color:#14233F;font-size:22px;font-weight:900;}QLabel#SectionTitle{color:#236FAF;font-size:13px;font-weight:900;}QListWidget{background:transparent;border:0;outline:0;}QListWidget::item{color:#C7D4E8;padding:13px 12px;margin:2px 0;border-radius:9px;font-size:13px;font-weight:700;}QListWidget::item:selected{background:#2588E8;color:#FFF;}QLineEdit,QComboBox,QSpinBox{background:#F8FAFD;color:#17213A;border:1px solid #CBD7E8;padding:8px;border-radius:8px;}QPushButton{background:#FFF;color:#236FAF;border:1px solid #C9D8EA;padding:9px 12px;border-radius:8px;font-weight:800;}QPushButton:hover{border-color:#FF4FA3;}QPushButton#Primary{background:#1878D1;color:#FFF;border:0;}QCheckBox{spacing:8px;color:#273650;font-weight:600;padding:5px 0;}")
        root = QHBoxLayout(self); root.setContentsMargins(16, 16, 16, 16); root.setSpacing(14)
        side = QFrame(); side.setObjectName("Sidebar"); side.setFixedWidth(205); sl = QVBoxLayout(side)
        b = QLabel("FB-BINGO"); b.setObjectName("Brand"); sl.addWidget(b)
        sb = QLabel("DISEÑADOR PROFESIONAL"); sb.setObjectName("SubBrand"); sl.addWidget(sb)
        self.section_list = QListWidget(); [self.section_list.addItem(QListWidgetItem(s)) for s in SECTIONS]
        self.section_list.currentRowChanged.connect(self._select_section); sl.addWidget(self.section_list, 1); root.addWidget(side)

        center = QFrame(); center.setObjectName("Panel"); cl = QVBoxLayout(center); top = QHBoxLayout()
        t = QLabel("DISEÑADOR DE CARTONES"); t.setObjectName("PageTitle"); top.addWidget(t, 1)
        self.model = QComboBox(); self.model.addItems(self.designs.keys()); self.model.currentTextChanged.connect(self._load_design); top.addWidget(self.model); cl.addLayout(top)
        self.stack = QStackedWidget()
        for builder in (self._general, self._colors, self._logo_page, self._numbering, self._qr, self._footer, self._size, self._preview_page):
            p = QWidget(); builder(p); self.stack.addWidget(p)
        cl.addWidget(self.stack, 1)
        actions = QHBoxLayout(); n = QPushButton("＋ NUEVO DISEÑO"); n.clicked.connect(self._new)
        r = QPushButton("RESTAURAR POR DEFECTO"); r.clicked.connect(self._restore); d = QPushButton("ELIMINAR"); d.clicked.connect(self._delete)
        s = QPushButton("GUARDAR DISEÑO"); s.setObjectName("Primary"); s.clicked.connect(self._save)
        actions.addWidget(n); actions.addStretch(); actions.addWidget(r); actions.addWidget(d); actions.addWidget(s); cl.addLayout(actions); root.addWidget(center, 1)

        prev = QFrame(); prev.setObjectName("Panel"); pl = QVBoxLayout(prev); ph = QHBoxLayout(); pt = QLabel("VISTA PREVIA DE IMPRESIÓN"); pt.setObjectName("PageTitle"); ph.addWidget(pt, 1)
        self.preview_info = QLabel("A4 · 2 columnas · 6 filas"); self.preview_info.setObjectName("Muted"); ph.addWidget(self.preview_info); pl.addLayout(ph)
        from PySide6.QtSvgWidgets import QSvgWidget
        self.preview_svg = QSvgWidget(); self.preview_svg.setMinimumSize(650, 720); pl.addWidget(self.preview_svg, 1)
        note = QLabel("Vista real con el mismo renderer de impresión. Los 6 cartones forman una serie y DUPLICAR repite exactamente la misma serie."); note.setObjectName("Muted"); note.setWordWrap(True); pl.addWidget(note); root.addWidget(prev, 2)

    def _title(self, p, text):
        l = QVBoxLayout(p); x = QLabel(text); x.setObjectName("SectionTitle"); l.addWidget(x); return l

    def _row(self, l, label, w):
        r = QHBoxLayout(); r.addWidget(QLabel(label), 1); r.addWidget(w, 2); l.addLayout(r)

    def _general(self, p):
        l = self._title(p, "CONFIGURACIÓN GENERAL"); self.type_bingo = QComboBox(); self.type_bingo.addItem("90 Bolas")
        self.layout_card = QComboBox(); self.layout_card.addItem("3 filas × 9 columnas · 15 números")
        self.internal_model = QComboBox(); self.internal_model.addItem("Modelo A · principal", CardModel.A); self.internal_model.addItem("Modelo B · especial", CardModel.B); self.internal_model.currentIndexChanged.connect(self._preview)
        self.title_text = QLineEdit(); self.title_text.textChanged.connect(self._preview); self.tagline_text = QLineEdit(); self.tagline_text.textChanged.connect(self._preview)
        for a, b in (("Tipo de Bingo", self.type_bingo), ("Diseño del cartón", self.layout_card), ("Modelo para referencia", self.internal_model), ("Marca superior", self.title_text), ("Subtítulo", self.tagline_text)): self._row(l, a, b)
        l.addStretch()

    def _colors(self, p):
        l = self._title(p, "COLORES ACTUALES"); self.bg = QLineEdit(); self.empty = QLineEdit(); self.accent = QLineEdit(); self.secondary = QLineEdit(); self.border = QLineEdit(); self.number = QLineEdit()
        for w in (self.bg, self.empty, self.accent, self.secondary, self.border, self.number): w.textChanged.connect(self._preview)
        for a, w in (("Fondo", self.bg), ("Espacios vacíos", self.empty), ("Rosa palo", self.accent), ("Celeste", self.secondary), ("Bordes", self.border), ("Números", self.number)):
            r = QHBoxLayout(); r.addWidget(QLabel(a), 1); r.addWidget(w); c = QPushButton("●"); c.setFixedWidth(36); c.clicked.connect(lambda _, x=w: self._pick_color(x)); r.addWidget(c); l.addLayout(r)
        l.addStretch()

    def _logo_page(self, p):
        l = self._title(p, "LOGO E IDENTIDAD"); self.logo_path = QLineEdit(); self.logo_path.setReadOnly(True); b = QPushButton("SELECCIONAR LOGO"); b.setObjectName("Primary"); b.clicked.connect(self._logo)
        r = QHBoxLayout(); r.addWidget(self.logo_path, 1); r.addWidget(b); l.addLayout(r); x = QLabel("El logo se integra en el encabezado sin ocupar espacios de juego."); x.setObjectName("Muted"); l.addWidget(x); l.addStretch()

    def _numbering(self, p):
        l = self._title(p, "NUMERACIÓN"); self.show_serial = QCheckBox("Mostrar número de cartón"); self.show_serial.setChecked(True); self.show_serial.toggled.connect(self._preview)
        self.number_format = QComboBox(); self.number_format.addItems(["Cartón grande + ID pequeño", "Solo número de cartón"]); self.preview_number = QLineEdit(self._preview_card_number); self.preview_number.textChanged.connect(self.set_preview_card_number)
        l.addWidget(self.show_serial); self._row(l, "Formato", self.number_format); self._row(l, "Número de ejemplo", self.preview_number); l.addStretch()

    def _qr(self, p):
        l = self._title(p, "QR Y SEGURIDAD"); self.show_qr = QCheckBox("Reservar espacio para QR"); self.show_qr.setChecked(True); self.security = QCheckBox("Mostrar ID de seguridad discreto"); self.security.setChecked(True)
        self.show_qr.toggled.connect(self._preview); self.security.toggled.connect(self._preview); l.addWidget(self.show_qr); l.addWidget(self.security)
        x = QLabel("El modelo A/B queda interno para verificación y nunca se imprime."); x.setObjectName("Muted"); x.setWordWrap(True); l.addWidget(x); l.addStretch()

    def _footer(self, p):
        l = self._title(p, "TEXTO INFERIOR"); self.footer_text = QLineEdit(); self.footer_text.textChanged.connect(self._preview); self.show_footer = QCheckBox("Mostrar pie del cartón"); self.show_footer.setChecked(True); self.show_footer.toggled.connect(self._preview); self.show_tagline = QCheckBox("Mostrar subtítulo de marca"); self.show_tagline.setChecked(True); self.show_tagline.toggled.connect(self._preview)
        self._row(l, "Texto", self.footer_text); l.addWidget(self.show_footer); l.addWidget(self.show_tagline); l.addStretch()

    def _size(self, p):
        l = self._title(p, "TAMAÑO Y PROPORCIONES"); self.width = QSpinBox(); self.width.setRange(100, 120); self.width.setValue(120); self.width.setSuffix(" mm"); self.height = QSpinBox(); self.height.setRange(70, 85); self.height.setValue(77); self.height.setSuffix(" mm"); self.font_size = QSpinBox(); self.font_size.setRange(8, 48); self.font_size.setValue(18); self.font_size.setSuffix(" pt"); self.font = QComboBox(); self.font.addItems(["Arial", "Segoe UI", "Calibri", "Tahoma", "Verdana"])
        for w in (self.width, self.height, self.font_size): w.valueChanged.connect(self._preview)
        self.font.currentTextChanged.connect(self._preview)
        for a, b in (("Ancho cartón", self.width), ("Alto cartón", self.height), ("Fuente", self.font), ("Tamaño números", self.font_size)): self._row(l, a, b)
        l.addStretch()

    def _preview_page(self, p):
        l = self._title(p, "VISTA PREVIA"); x = QLabel("La vista de la derecha es la referencia final para imprimir."); x.setObjectName("Muted"); x.setWordWrap(True); l.addWidget(x); b = QPushButton("ACTUALIZAR VISTA"); b.setObjectName("Primary"); b.clicked.connect(self._preview); l.addWidget(b); l.addStretch()

    @staticmethod
    def _grid():
        # Modelo A: máximo 2 números por columna, mínimo 1, 5 por fila.
        return (
            (1, 13, 22, 34, 45, None, None, None, None),
            (5, 19, None, None, None, 56, 67, 78, None),
            (None, None, 28, 39, 48, 59, None, None, 90),
        )

    def _style(self):
        return PrintStyle(background_color=self.bg.text() or "#FFFFFF", empty_cell_color=self.empty.text() or "#F7DDE7", number_color=self.number.text() or "#171B2B", border_color=self.border.text() or "#8FD9FF", accent_color=self.accent.text() or "#FF4FA3", secondary_accent_color=self.secondary.text() or "#8FD9FF", logo_path=self.logo_path.text() or None, show_model=False, show_serial=self.show_serial.isChecked(), show_qr_zone=self.show_qr.isChecked(), brand_title=self.title_text.text() or "FB-BINGO", brand_tagline=self.tagline_text.text() or "¡LA DIVERSIÓN QUE NOS UNE!", footer_text=self.footer_text.text() or "BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA", show_footer=self.show_footer.isChecked(), show_tagline=self.show_tagline.isChecked(), font_family=self.font.currentText() or "Arial", number_font_size=float(self.font_size.value() or 18))

    def _preview(self, *_):
        if not hasattr(self, "preview_svg"):
            return
        try:
            cards = tuple(BingoCard(serial=f"0001-{int(self._preview_card_number or 11534) + i:06d}", model=CardModel.A, grid=self._grid()) for i in range(6))
            svg = A4SvgRenderer(style=self._style()).render_columns(cards, cards)
            self._preview_svg_text = svg
            self.preview_svg.load(svg.encode("utf-8"))
        except (ValueError, TypeError):
            self._preview_svg_text = ""

    def section_buttons_text(self):
        return [self.section_list.item(i).text() for i in range(self.section_list.count())]

    def preview_is_real_card(self):
        return hasattr(self, "_preview_svg_text") and 'class="bingo-card"' in self._preview_svg_text

    def preview_has_grid(self, rows, columns):
        return hasattr(self, "_preview_svg_text") and self._preview_svg_text.count("<rect x=") >= rows * columns

    def preview_svg(self):
        return getattr(self, "_preview_svg_text", "")

    def set_preview_card_number(self, number):
        self._preview_card_number = "".join(ch for ch in str(number) if ch.isdigit()) or "11534"; self._preview()

    def current_design(self):
        return {"font": self.font.currentText(), "font_size": self.font_size.value(), "width_mm": self.width.value(), "height_mm": self.height.value(), "title": self.title_text.text(), "tagline": self.tagline_text.text(), "footer": self.footer_text.text(), "logo": self.logo_path.text(), "bg": self.bg.text(), "empty": self.empty.text(), "accent": self.accent.text(), "secondary_accent": self.secondary.text(), "border": self.border.text(), "number": self.number.text(), "show_serial": self.show_serial.isChecked(), "show_qr": self.show_qr.isChecked(), "show_model": False, "show_footer": self.show_footer.isChecked(), "show_tagline": self.show_tagline.isChecked()}

    def _load_design(self, name):
        if name not in self.designs or not hasattr(self, "font"):
            return
        d = self.designs[name]; self.font.setCurrentText(d.get("font", "Arial")); self.font_size.setValue(int(d.get("font_size", 18))); self.width.setValue(int(d.get("width_mm", 120))); self.height.setValue(int(d.get("height_mm", 77))); self.title_text.setText(d.get("title", "FB-BINGO")); self.tagline_text.setText(d.get("tagline", "¡LA DIVERSIÓN QUE NOS UNE!")); self.footer_text.setText(d.get("footer", "BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA")); self.logo_path.setText(d.get("logo", "")); self.bg.setText(d.get("bg", "#FFFFFF")); self.empty.setText(d.get("empty", "#F7DDE7")); self.accent.setText(d.get("accent", "#FF4FA3")); self.secondary.setText(d.get("secondary_accent", "#8FD9FF")); self.border.setText(d.get("border", "#8FD9FF")); self.number.setText(d.get("number", "#171B2B")); self.show_serial.setChecked(bool(d.get("show_serial", True))); self.show_qr.setChecked(bool(d.get("show_qr", True))); self.show_footer.setChecked(bool(d.get("show_footer", True))); self.show_tagline.setChecked(bool(d.get("show_tagline", True))); self._preview()

    def _save(self):
        self.designs[self.model.currentText()] = self.current_design()
        try:
            self._persist()
        except OSError as exc:
            QMessageBox.warning(self, "FB-BINGO", f"No se pudo guardar el diseño:\n{exc}")
        self.designChanged.emit(); self._preview()

    def _new(self):
        name = "Nuevo diseño"; index = 2
        while name in self.designs:
            name = f"Nuevo diseño {index}"; index += 1
        self.designs[name] = dict(self._defaults()["FB-BINGO Profesional"]); self.model.addItem(name); self.model.setCurrentText(name); self._save()

    def _restore(self):
        self.designs[self.model.currentText()] = dict(self._defaults()["FB-BINGO Profesional"]); self._load_design(self.model.currentText()); self._save()

    def _delete(self):
        if self.model.count() <= 1:
            return
        name = self.model.currentText(); self.designs.pop(name, None); self.model.removeItem(self.model.currentIndex()); self._save()

    def _pick_color(self, target):
        color = QColorDialog.getColor()
        if color.isValid():
            target.setText(color.name().upper())

    def _select_section(self, index):
        if index >= 0:
            self.stack.setCurrentIndex(index); self._preview()

    def _logo(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg *.svg)")
        if path:
            self.logo_path.setText(path); self._preview()
