from __future__ import annotations

import json
from html import escape
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QColorDialog,
    QComboBox,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer, PrintStyle
from app.settings.paths import application_data_dir


SECTIONS = (
    "General",
    "Colores",
    "Logo",
    "Numeración",
    "QR y Seguridad",
    "Texto inferior",
    "Tamaño",
    "Vista previa",
)


class DesignerWindow(QWidget):
    """Diseñador profesional de cartones; los cambios visuales no alteran la lógica del bingo."""

    designChanged = Signal()

    def __init__(self):
        super().__init__()
        self.setWindowTitle("FB-BINGO — Diseñador Profesional de Cartones")
        self.resize(1480, 900)
        self.setMinimumSize(1180, 760)
        self.path = application_data_dir() / "card_designs.json"
        self.designs = self._load()
        self._preview_card_number = "11534"
        self._logo_path = ""
        self._build()
        self._load_design(self.model.currentText())
        self._select_section(0)

    # ---------- persistence ----------
    def _defaults(self) -> dict[str, dict]:
        return {
            "FB-BINGO Profesional": {
                "font": "Arial",
                "font_size": 18,
                "width_cm": 12.0,
                "height_cm": 7.7,
                "title": "FB-BINGO",
                "tagline": "¡LA DIVERSIÓN QUE NOS UNE!",
                "footer": "BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA",
                "logo": "",
                "bg": "#FFFFFF",
                "empty": "#F7DDE7",
                "accent": "#FF4FA3",
                "secondary_accent": "#8FD9FF",
                "border": "#8FD9FF",
                "number": "#171B2B",
                "show_serial": True,
                "show_qr": True,
                "show_model": False,
                "show_footer": True,
                "show_tagline": True,
            }
        }

    def _load(self):
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and data:
                defaults = self._defaults()
                for name, design in data.items():
                    if isinstance(design, dict):
                        merged = dict(defaults["FB-BINGO Profesional"])
                        merged.update(design)
                        data[name] = merged
                return data
        except (OSError, ValueError, TypeError):
            pass
        return self._defaults()

    def _persist(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self.designs, ensure_ascii=False, indent=2), encoding="utf-8")

    # ---------- UI ----------
    def _build(self) -> None:
        self.setStyleSheet(
            """
            QWidget { background:#F4F7FC; color:#17213A; font-family:'Segoe UI'; }
            QFrame#Sidebar { background:#0C1730; border:0; border-radius:16px; }
            QLabel#Brand { color:#FFFFFF; font-size:20px; font-weight:900; padding:6px 8px; }
            QLabel#SubBrand { color:#9EB5D5; font-size:11px; padding:0 8px 10px; }
            QListWidget { background:transparent; border:0; outline:0; padding:6px; }
            QListWidget::item { color:#C7D4E8; padding:13px 12px; margin:2px 0; border-radius:9px; font-size:13px; font-weight:700; }
            QListWidget::item:selected { background:#2588E8; color:white; }
            QFrame#Panel { background:white; border:1px solid #DCE4F0; border-radius:16px; }
            QLabel#PageTitle { color:#14233F; font-size:22px; font-weight:900; }
            QLabel#SectionTitle { color:#236FAF; font-size:13px; font-weight:900; }
            QLabel#Muted { color:#71819A; font-size:11px; }
            QLabel#Value { color:#17213A; font-size:13px; font-weight:800; }
            QLineEdit,QComboBox,QSpinBox { background:#F8FAFD; color:#17213A; border:1px solid #CBD7E8; padding:8px 9px; border-radius:8px; min-height:18px; }
            QLineEdit:focus,QComboBox:focus,QSpinBox:focus { border:2px solid #8FD9FF; }
            QPushButton { background:#FFFFFF; color:#236FAF; border:1px solid #C9D8EA; padding:9px 12px; border-radius:8px; font-weight:800; }
            QPushButton:hover { border-color:#FF4FA3; }
            QPushButton#Primary { background:#1878D1; color:white; border:0; }
            QPushButton#Pink { background:#FF4FA3; color:white; border:0; }
            QCheckBox { spacing:8px; color:#273650; font-weight:600; padding:5px 0; }
            QScrollArea { border:0; background:transparent; }
            """
        )
        root = QHBoxLayout(self)
        root.setContentsMargins(16, 16, 16, 16)
        root.setSpacing(14)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(205)
        sl = QVBoxLayout(sidebar)
        sl.setContentsMargins(10, 18, 10, 14)
        brand = QLabel("FB-BINGO")
        brand.setObjectName("Brand")
        sl.addWidget(brand)
        sub = QLabel("DISEÑADOR PROFESIONAL")
        sub.setObjectName("SubBrand")
        sl.addWidget(sub)
        self.section_list = QListWidget()
        self.section_list.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        for section in SECTIONS:
            item = QListWidgetItem(section)
            self.section_list.addItem(item)
        self.section_list.currentRowChanged.connect(self._select_section)
        sl.addWidget(self.section_list, 1)
        help_label = QLabel("Los cambios son visuales.\nLa generación A/B no se modifica desde aquí.")
        help_label.setObjectName("SubBrand")
        help_label.setWordWrap(True)
        sl.addWidget(help_label)
        root.addWidget(sidebar)

        center = QFrame()
        center.setObjectName("Panel")
        cl = QVBoxLayout(center)
        cl.setContentsMargins(18, 18, 18, 18)
        cl.setSpacing(12)
        header = QHBoxLayout()
        title = QLabel("DISEÑADOR DE CARTONES")
        title.setObjectName("PageTitle")
        header.addWidget(title, 1)
        self.model = QComboBox()
        self.model.addItems(self.designs.keys())
        self.model.currentTextChanged.connect(self._load_design)
        header.addWidget(self.model)
        cl.addLayout(header)
        self.stack = QStackedWidget()
        self._pages: list[QWidget] = []
        for builder in (
            self._page_general,
            self._page_colors,
            self._page_logo,
            self._page_numbering,
            self._page_qr,
            self._page_footer,
            self._page_size,
            self._page_preview,
        ):
            page = QWidget()
            builder(page)
            self._pages.append(page)
            self.stack.addWidget(page)
        cl.addWidget(self.stack, 1)
        actions = QHBoxLayout()
        new_btn = QPushButton("＋ NUEVO DISEÑO")
        new_btn.clicked.connect(self._new)
        save_btn = QPushButton("GUARDAR DISEÑO")
        save_btn.setObjectName("Primary")
        save_btn.clicked.connect(self._save)
        restore_btn = QPushButton("RESTAURAR POR DEFECTO")
        restore_btn.clicked.connect(self._restore)
        delete_btn = QPushButton("ELIMINAR")
        delete_btn.clicked.connect(self._delete)
        actions.addWidget(new_btn)
        actions.addStretch(1)
        actions.addWidget(restore_btn)
        actions.addWidget(delete_btn)
        actions.addWidget(save_btn)
        cl.addLayout(actions)
        root.addWidget(center, 1)

        preview_panel = QFrame()
        preview_panel.setObjectName("Panel")
        pr = QVBoxLayout(preview_panel)
        pr.setContentsMargins(16, 16, 16, 16)
        ph = QHBoxLayout()
        ptitle = QLabel("VISTA PREVIA DE IMPRESIÓN")
        ptitle.setObjectName("PageTitle")
        ph.addWidget(ptitle, 1)
        self.preview_info = QLabel("A4 · 2 columnas · 6 filas")
        self.preview_info.setObjectName("Muted")
        ph.addWidget(self.preview_info)
        pr.addLayout(ph)
        self.preview_svg_widget = QSvgWidget()
        self.preview_svg_widget.setMinimumSize(650, 720)
        self.preview_svg_widget.setStyleSheet("background:#E9EEF5;border-radius:12px;")
        pr.addWidget(self.preview_svg_widget, 1)
        note = QLabel("La vista previa utiliza el mismo renderer que la impresión A4. El modelo interno nunca se imprime.")
        note.setObjectName("Muted")
        note.setWordWrap(True)
        pr.addWidget(note)
        root.addWidget(preview_panel, 2)

    def _label(self, text: str) -> QLabel:
        label = QLabel(text)
        label.setObjectName("SectionTitle")
        return label

    def _page_general(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("CONFIGURACIÓN GENERAL"))
        self.type_bingo = QComboBox(); self.type_bingo.addItem("90 Bolas")
        self.layout_card = QComboBox(); self.layout_card.addItem("3 filas × 9 columnas · 15 números")
        self.internal_model = QComboBox(); self.internal_model.addItem("Modelo A · principal", CardModel.A); self.internal_model.addItem("Modelo B · especial", CardModel.B)
        self.title_text = QLineEdit()
        self.tagline_text = QLineEdit()
        self._form_rows(l, [("Tipo de Bingo", self.type_bingo), ("Diseño del cartón", self.layout_card), ("Modelo para referencia", self.internal_model), ("Marca superior", self.title_text), ("Subtítulo", self.tagline_text)])
        l.addStretch(1)

    def _page_colors(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("COLORES ACTUALES"))
        self.bg = QLineEdit(); self.empty = QLineEdit(); self.accent = QLineEdit(); self.secondary = QLineEdit(); self.border = QLineEdit(); self.number = QLineEdit()
        for w in (self.bg, self.empty, self.accent, self.secondary, self.border, self.number):
            w.textChanged.connect(self._preview)
        self._color_rows = []
        for label, widget in (("Fondo", self.bg), ("Espacios vacíos", self.empty), ("Acento rosa palo", self.accent), ("Acento celeste", self.secondary), ("Bordes", self.border), ("Números", self.number)):
            row = QHBoxLayout(); row.addWidget(QLabel(label), 1); row.addWidget(widget); b = QPushButton("●"); b.setFixedWidth(36); b.clicked.connect(lambda _, x=widget: self._pick_color(x)); row.addWidget(b); l.addLayout(row)
        l.addStretch(1)

    def _page_logo(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("LOGO E IDENTIDAD"))
        self.logo_path = QLineEdit(); self.logo_path.setReadOnly(True)
        b = QPushButton("SELECCIONAR LOGO")
        b.setObjectName("Primary"); b.clicked.connect(self._logo)
        row = QHBoxLayout(); row.addWidget(self.logo_path, 1); row.addWidget(b); l.addLayout(row)
        self.logo_hint = QLabel("Recomendado: logo PNG transparente o SVG. Se colocará en el encabezado del cartón.")
        self.logo_hint.setObjectName("Muted"); self.logo_hint.setWordWrap(True); l.addWidget(self.logo_hint)
        l.addStretch(1)

    def _page_numbering(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("NUMERACIÓN"))
        self.show_serial = QCheckBox("Mostrar número de cartón")
        self.show_serial.setChecked(True); self.show_serial.toggled.connect(self._preview)
        self.number_format = QComboBox(); self.number_format.addItems(["Cartón grande + ID pequeño", "Solo número de cartón"])
        self.preview_number = QLineEdit(self._preview_card_number); self.preview_number.setPlaceholderText("Ej. 11534"); self.preview_number.textChanged.connect(self.set_preview_card_number)
        l.addWidget(self.show_serial); self._form_rows(l, [("Formato", self.number_format), ("Número de ejemplo", self.preview_number)])
        l.addStretch(1)

    def _page_qr(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("QR Y SEGURIDAD"))
        self.show_qr = QCheckBox("Reservar espacio para QR")
        self.show_qr.setChecked(True); self.show_qr.toggled.connect(self._preview)
        self.show_model = QCheckBox("Mostrar modelo interno en impresión (no recomendado)")
        self.show_model.setChecked(False); self.show_model.setEnabled(False)
        self.security = QCheckBox("Mostrar ID de seguridad discreto")
        self.security.setChecked(True); self.security.toggled.connect(self._preview)
        l.addWidget(self.show_qr); l.addWidget(self.show_model); l.addWidget(self.security)
        warning = QLabel("El Modelo A/B se conserva internamente para verificación, pero no forma parte del diseño físico del cartón.")
        warning.setObjectName("Muted"); warning.setWordWrap(True); l.addWidget(warning); l.addStretch(1)

    def _page_footer(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("TEXTO INFERIOR"))
        self.footer_text = QLineEdit(); self.footer_text.textChanged.connect(self._preview)
        self.show_footer = QCheckBox("Mostrar pie del cartón"); self.show_footer.setChecked(True); self.show_footer.toggled.connect(self._preview)
        self.show_tagline = QCheckBox("Mostrar subtítulo de marca"); self.show_tagline.setChecked(True); self.show_tagline.toggled.connect(self._preview)
        self._form_rows(l, [("Texto", self.footer_text)])
        l.addWidget(self.show_footer); l.addWidget(self.show_tagline); l.addStretch(1)

    def _page_size(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("TAMAÑO Y PROPORCIONES"))
        self.width = QSpinBox(); self.width.setRange(80, 180); self.width.setSuffix(" mm"); self.width.valueChanged.connect(self._preview)
        self.height = QSpinBox(); self.height.setRange(50, 100); self.height.setSuffix(" mm"); self.height.valueChanged.connect(self._preview)
        self.font_size = QSpinBox(); self.font_size.setRange(8, 48); self.font_size.setSuffix(" pt"); self.font_size.valueChanged.connect(self._preview)
        self.font = QComboBox(); self.font.addItems(["Arial", "Segoe UI", "Calibri", "Tahoma", "Verdana"]); self.font.currentTextChanged.connect(self._preview)
        self._form_rows(l, [("Ancho cartón", self.width), ("Alto cartón", self.height), ("Fuente", self.font), ("Tamaño números", self.font_size)])
        hint = QLabel("El formato recomendado mantiene una tarjeta compacta y limpia para troquelado. La geometría A4 se mantiene independiente.")
        hint.setObjectName("Muted"); hint.setWordWrap(True); l.addWidget(hint); l.addStretch(1)

    def _page_preview(self, page: QWidget) -> None:
        l = QVBoxLayout(page)
        l.addWidget(self._label("VISTA PREVIA"))
        info = QLabel("La vista de la derecha es la referencia final. Aquí puedes revisar rápidamente el aspecto del cartón.")
        info.setObjectName("Muted"); info.setWordWrap(True); l.addWidget(info)
        refresh = QPushButton("ACTUALIZAR VISTA")
        refresh.setObjectName("Primary"); refresh.clicked.connect(self._preview); l.addWidget(refresh)
        l.addStretch(1)

    def _form_rows(self, layout: QVBoxLayout, rows: list[tuple[str, QWidget]]) -> None:
        for label, widget in rows:
            row = QHBoxLayout(); lab = QLabel(label); lab.setMinimumWidth(145); row.addWidget(lab); row.addWidget(widget, 1); layout.addLayout(row)

    def _select_section(self, index: int) -> None:
        if index < 0:
            return
        self.stack.setCurrentIndex(index)
        self._preview()

    # ---------- preview ----------
    @staticmethod
    def _sample_card(serial: str, model: CardModel) -> BingoCard:
        grid = (
            (1, None, 22, None, 44, 55, None, 77, None),
            (2, 13, None, 34, None, 56, 66, None, 89),
            (None, 19, 28, 39, 48, None, 68, None, 90),
        )
        # This sample is deliberately valid for Model A: every row has 5 numbers,
        # every column has 1–2 numbers, and each column is within its range.
        return BingoCard(serial=serial, model=model, grid=grid)

    def _style(self) -> PrintStyle:
        return PrintStyle(
            background_color=self.bg.text() or "#FFFFFF",
            empty_cell_color=self.empty.text() or "#F7DDE7",
            number_color=self.number.text() or "#171B2B",
            border_color=self.border.text() or "#8FD9FF",
            accent_color=self.accent.text() or "#FF4FA3",
            secondary_accent_color=self.secondary.text() or "#8FD9FF",
            logo_path=self.logo_path.text() or None,
            show_model=False,
            show_serial=self.show_serial.isChecked(),
            show_qr_zone=self.show_qr.isChecked(),
        )

    def _preview(self, *_args) -> None:
        if not hasattr(self, "preview_svg_widget"):
            return
        try:
            model = CardModel(self.internal_model.currentData())
            card = self._sample_card(f"0001-{self._preview_card_number:0>6}", model)
            # The designer preview is rendered by the exact production renderer.
            renderer = A4SvgRenderer(style=self._style())
            cards = tuple(
                BingoCard(
                    serial=f"0001-{int(self._preview_card_number or 11534) + i:06d}",
                    model=model,
                    grid=card.grid,
                )
                for i in range(6)
            )
            svg = renderer.render_columns(cards, cards)
            self._preview_svg = svg
            self.preview_svg_widget.load(svg.encode("utf-8"))
            self.preview_info.setText("A4 · 2 columnas · 6 filas · misma vista que impresión")
        except (ValueError, TypeError):
            return

    # ---------- public test/UI helpers ----------
    def section_buttons_text(self) -> list[str]:
        return [self.section_list.item(i).text() for i in range(self.section_list.count())]

    def preview_is_real_card(self) -> bool:
        return hasattr(self, "_preview_svg") and 'class="bingo-card"' in self._preview_svg

    def preview_has_grid(self, rows: int, columns: int) -> bool:
        if not hasattr(self, "_preview_svg"):
            return False
        return self._preview_svg.count('<rect x="') >= rows * columns

    def preview_svg(self) -> str:
        return getattr(self, "_preview_svg", "")

    def set_preview_card_number(self, number: str) -> None:
        value = "".join(ch for ch in str(number) if ch.isdigit()) or "11534"
        self._preview_card_number = value
        if hasattr(self, "preview_number") and self.preview_number.text() != value:
            self.preview_number.blockSignals(True); self.preview_number.setText(value); self.preview_number.blockSignals(False)
        self._preview()

    def current_design(self) -> dict:
        return {
            "font": self.font.currentText(),
            "font_size": self.font_size.value(),
            "width_mm": self.width.value(),
            "height_mm": self.height.value(),
            "title": self.title_text.text(),
            "tagline": self.tagline_text.text(),
            "footer": self.footer_text.text(),
            "logo": self.logo_path.text(),
            "bg": self.bg.text(),
            "empty": self.empty.text(),
            "accent": self.accent.text(),
            "secondary_accent": self.secondary.text(),
            "border": self.border.text(),
            "number": self.number.text(),
            "show_serial": self.show_serial.isChecked(),
            "show_qr": self.show_qr.isChecked(),
            "show_model": False,
            "show_footer": self.show_footer.isChecked(),
            "show_tagline": self.show_tagline.isChecked(),
        }

    # ---------- persistence/actions ----------
    def _load_design(self, name: str) -> None:
        if name not in self.designs or not hasattr(self, "font"):
            return
        d = self.designs[name]
        self.font.setCurrentText(d.get("font", "Arial"))
        self.font_size.setValue(int(d.get("font_size", 18)))
        self.width.setValue(int(d.get("width_mm", round(float(d.get("width_cm", 12)) * 10))))
        self.height.setValue(int(d.get("height_mm", round(float(d.get("height_cm", 7.7)) * 10))))
        self.title_text.setText(d.get("title", "FB-BINGO"))
        self.tagline_text.setText(d.get("tagline", "¡LA DIVERSIÓN QUE NOS UNE!"))
        self.footer_text.setText(d.get("footer", "BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA"))
        self.logo_path.setText(d.get("logo", ""))
        self.bg.setText(d.get("bg", "#FFFFFF")); self.empty.setText(d.get("empty", "#F7DDE7")); self.accent.setText(d.get("accent", "#FF4FA3")); self.secondary.setText(d.get("secondary_accent", "#8FD9FF")); self.border.setText(d.get("border", "#8FD9FF")); self.number.setText(d.get("number", "#171B2B"))
        self.show_serial.setChecked(bool(d.get("show_serial", True)))
        self.show_qr.setChecked(bool(d.get("show_qr", True)))
        self.show_footer.setChecked(bool(d.get("show_footer", True)))
        self.show_tagline.setChecked(bool(d.get("show_tagline", True)))
        self.internal_model.setCurrentIndex(0)
        self._preview()

    def _save(self) -> None:
        self.designs[self.model.currentText()] = self.current_design()
        try:
            self._persist()
        except OSError as exc:
            QMessageBox.warning(self, "FB-BINGO", f"No se pudo guardar el diseño:\n{exc}")
            return
        self.designChanged.emit()
        QMessageBox.information(self, "FB-BINGO", "Diseño guardado correctamente.")

    def _restore(self) -> None:
        default = self._defaults()["FB-BINGO Profesional"]
        self.designs[self.model.currentText()] = dict(default)
        self._load_design(self.model.currentText())

    def _new(self) -> None:
        name = f"Diseño {len(self.designs) + 1}"
        while name in self.designs:
            name = f"Diseño {len(self.designs) + 1}"
        self.designs[name] = dict(self._defaults()["FB-BINGO Profesional"])
        self.model.addItem(name)
        self.model.setCurrentText(name)

    def _delete(self) -> None:
        name = self.model.currentText()
        if len(self.designs) <= 1:
            return
        self.designs.pop(name, None)
        index = self.model.currentIndex()
        self.model.removeItem(index)
        self._persist()

    def _logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg *.svg)")
        if path:
            self.logo_path.setText(path)
            self._preview()

    def _pick_color(self, target: QLineEdit) -> None:
        color = QColorDialog.getColor()
        if color.isValid():
            target.setText(color.name().upper())


__all__ = ["DesignerWindow"]
