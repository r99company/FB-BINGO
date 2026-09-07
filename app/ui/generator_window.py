from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import DuplicateProductionError, ProductionService
from app.settings.paths import database_path


class GeneratorWidget(QWidget):
    """Generador de producción y previsualización A4 de 12 posiciones físicas."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None, max_cards: int = 15_000) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(database_path())
        self.production_service = ProductionService(self.repository, max_cards=max_cards)
        self._series = None
        self._logo_path: str | None = None
        self._svg = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        controls = QGroupBox("GENERADOR DE CARTONES")
        controls.setMinimumWidth(360)
        form = QFormLayout(controls)

        self.model = QComboBox()
        self.model.addItem("Modelo A", CardModel.A.value)
        series_capacity = self.production_service.max_cards // 6
        serial_max = self.production_service.max_cards - 5

        self.series_id = QSpinBox(); self.series_id.setRange(1, series_capacity); self.series_id.setValue(1)
        self.series_id.valueChanged.connect(self._sync_serial_from_series)
        self.quantity = QSpinBox(); self.quantity.setRange(1, series_capacity); self.quantity.setValue(1)
        self.serial_start = QSpinBox(); self.serial_start.setRange(1, serial_max); self.serial_start.setValue(1)
        self.serial_start.valueChanged.connect(self._sync_series_from_serial)

        self.empty_color = QLineEdit("#F2E9FF")
        self.accent_color = QLineEdit("#FF4FA3")
        self.secondary_color = QLineEdit("#8FD9FF")
        self.logo = QLabel("Sin logo seleccionado"); self.logo.setObjectName("Muted"); self.logo.setWordWrap(True)

        self.qr = QComboBox()
        self.qr.addItem("SIN QR — sin zona reservada", False)
        self.qr.addItem("CON QR — reservar zona", True)

        self.duplicate_column = QCheckBox("DUPLICAR COLUMNA — izquierda y derecha iguales")
        self.duplicate_column.setChecked(False)
        self.duplicate_column.setToolTip("Sí: 1–6 a la izquierda y 1–6 a la derecha. No: 1–6 a la izquierda y 7–12 a la derecha.")

        logo_button = QPushButton("SELECCIONAR LOGO"); logo_button.setObjectName("Secondary"); logo_button.clicked.connect(self._choose_logo)
        generate = QPushButton("GENERAR PRODUCCIÓN"); generate.setObjectName("Primary"); generate.clicked.connect(self.generate_series)
        preview = QPushButton("ACTUALIZAR VISTA A4"); preview.setObjectName("Secondary"); preview.clicked.connect(self.preview_a4)
        save = QPushButton("GUARDAR A4 (SVG)"); save.setObjectName("Secondary"); save.clicked.connect(self.save_a4)

        for label, widget in (("Modelo", self.model), ("Serie inicial", self.series_id), ("Cantidad de series", self.quantity), ("Serial inicial", self.serial_start), ("Color espacios", self.empty_color), ("Color principal", self.accent_color), ("Color secundario", self.secondary_color), ("QR", self.qr)):
            form.addRow(label, widget)
        form.addRow("Impresión", self.duplicate_column)
        form.addRow(self.logo, logo_button); form.addRow(generate); form.addRow(preview); form.addRow(save)

        info = QLabel("Cada serie contiene 6 cartones. La hoja A4 de producción usa 2 columnas × 6 filas: modo normal coloca 1–6 a la izquierda y 7–12 a la derecha; Duplicar columna coloca 1–6 en ambos lados. Los cartones se leen de SQLite y nunca se regeneran al imprimir.")
        info.setObjectName("Muted"); info.setWordWrap(True); form.addRow(info)
        layout.addWidget(controls)

        preview_panel = QGroupBox("VISTA PREVIA — A4 / 12 POSICIONES")
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_widget = QSvgWidget(); self.preview_widget.setMinimumSize(650, 760); self.preview_widget.setStyleSheet("background:#FFFFFF;border:1px solid #34405B;border-radius:12px;")
        preview_layout.addWidget(self.preview_widget, 1)
        self.preview_label = QLabel("Genera una serie para visualizar la hoja A4."); self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview_label.setObjectName("Muted"); preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_panel, 1)

    def _sync_serial_from_series(self, series_number: int) -> None:
        expected_serial = (series_number - 1) * 6 + 1
        self.serial_start.blockSignals(True); self.serial_start.setValue(expected_serial); self.serial_start.blockSignals(False)

    def _sync_series_from_serial(self, serial: int) -> None:
        if serial < 1: return
        series_number = (serial - 1) // 6 + 1
        self.series_id.blockSignals(True); self.series_id.setValue(min(series_number, self.series_id.maximum())); self.series_id.blockSignals(False)

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path; self.logo.setText(Path(path).name); self.preview_a4()

    def _style(self) -> PrintStyle:
        return PrintStyle(empty_cell_color=self.empty_color.text().strip() or "#F2E9FF", accent_color=self.accent_color.text().strip() or "#FF4FA3", secondary_accent_color=self.secondary_color.text().strip() or "#8FD9FF", logo_path=self._logo_path, show_model=False, show_serial=True, show_qr_zone=bool(self.qr.currentData()))

    def generate_series(self) -> None:
        model = CardModel(self.model.currentData()); start_card = self.serial_start.value(); card_count = self.quantity.value() * 6; end_card = start_card + card_count - 1; expected_series = (start_card - 1) // 6 + 1
        if expected_series != self.series_id.value():
            QMessageBox.warning(self, "Numeración no válida", "La serie inicial y el serial inicial no corresponden a una numeración continua de 6 cartones por serie."); return
        if end_card > self.production_service.max_cards:
            QMessageBox.warning(self, "Capacidad superada", f"La producción inicial permite hasta {self.production_service.max_cards:,} cartones. El rango solicitado termina en {end_card:,}."); return
        try:
            lot = self.production_service.create_lot(start_card, end_card, model=model, operator="generador-ui")
            result = self.production_service.generate_lot(lot.lot_id)
            self._series = self.repository.get(f"{expected_series:04d}")
            self._render_preview()
            modo = "COLUMNA DUPLICADA" if self.duplicate_column.isChecked() else "NORMAL"
            self.preview_label.setText(f"PRODUCCIÓN REGISTRADA · {result.series_count} serie(s) · {result.card_count} cartones · Serie {expected_series}–{expected_series + result.series_count - 1} · A4 {modo}")
        except DuplicateProductionError as exc: QMessageBox.warning(self, "Producción duplicada", str(exc))
        except (ValueError, RuntimeError, KeyError) as exc: QMessageBox.warning(self, "No se pudo generar", str(exc))

    def _next_series(self):
        if self._series is None: return None
        try: return self.repository.get(f"{int(self._series.series_id) + 1:04d}")
        except KeyError: return None

    def _render_preview(self) -> None:
        if self._series is None: raise ValueError("No se pudo generar la serie")
        renderer = A4SvgRenderer(style=self._style())
        right = self._series.cards if self.duplicate_column.isChecked() else (self._next_series().cards if self._next_series() is not None else None)
        self._svg = renderer.render_columns(self._series.cards, right, duplicate_column=self.duplicate_column.isChecked()) if right is not None else renderer.render(self._series.cards)
        self.preview_widget.load(self._svg.encode("utf-8"))

    def preview_a4(self) -> None:
        try:
            if self._series is None: self.generate_series(); return
            self._render_preview()
            modo = "COLUMNA DUPLICADA" if self.duplicate_column.isChecked() else "NORMAL"
            derecha = "1–6" if self.duplicate_column.isChecked() else "7–12"
            self.preview_label.setText(f"Vista A4 · izquierda 1–6 · derecha {derecha} · {modo}")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error de vista previa", str(exc))

    def save_a4(self) -> None:
        try:
            if self._series is None: self.generate_series()
            if self._series is None: raise ValueError("No hay una serie generada")
            svg = self._svg or A4SvgRenderer(style=self._style()).render(self._series.cards)
            path, _ = QFileDialog.getSaveFileName(self, "Guardar hoja A4", f"fb_bingo_serie_{self._series.series_id}.svg", "SVG (*.svg)")
            if path:
                Path(path).write_text(svg, encoding="utf-8"); QMessageBox.information(self, "A4 guardado", "La hoja A4 fue guardada correctamente.")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error al guardar", str(exc))


GeneratorWindow = GeneratorWidget
