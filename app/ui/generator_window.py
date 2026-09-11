from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QApplication, QCheckBox, QComboBox, QFileDialog, QFormLayout, QGroupBox,
    QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox,
    QToolButton, QVBoxLayout, QWidget,
)

from app.cards import BingoCard, CardModel
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import DuplicateProductionError, ProductionService
from app.settings.paths import database_path


class GeneratorWidget(QWidget):
    """Generador de series. El mismo rango siempre representa los mismos cartones."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None, max_cards: int = 30_000) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(database_path())
        self.production_service = ProductionService(self.repository, max_cards=max_cards)
        self._cards: tuple[BingoCard, ...] = ()
        self._loaded_start_card: int | None = None
        self._loaded_card_count: int | None = None
        self._logo_path: str | None = None
        self._svg = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        controls = QGroupBox("GENERACIÓN DE SERIES")
        controls.setMinimumWidth(420)
        form = QFormLayout(controls)

        self.model = QComboBox()
        self.model.addItem("Modelo A · PRINCIPAL", CardModel.A.value)
        self.model.addItem("Modelo B · ESPECIAL", CardModel.B.value)

        self.start_card = QSpinBox()
        self.start_card.setRange(1, self.production_service.max_cards)
        self.start_card.setSingleStep(6)
        self.start_card.setValue(1)
        self.start_card.valueChanged.connect(self._normalize_start)

        self.series_count = QSpinBox()
        self.series_count.setRange(1, self.production_service.max_cards // 6)
        self.series_count.setValue(1)
        self.series_count.setSingleStep(1)
        self.series_count.valueChanged.connect(self._update_range_label)

        self.range_label = QLabel(); self.range_label.setObjectName("Muted")
        self.cards_label = QLabel(); self.cards_label.setObjectName("Muted")
        self.pages_label = QLabel(); self.pages_label.setObjectName("Muted")
        form.addRow("Comenzar desde cartón", self.start_card)
        form.addRow("Cantidad de series", self.series_count)
        form.addRow("Modelo", self.model)
        form.addRow("Rango", self.range_label)
        form.addRow("Cartones generados", self.cards_label)
        form.addRow("Hojas A4", self.pages_label)

        next_free = QPushButton("PRÓXIMA SERIE LIBRE")
        next_free.setObjectName("Secondary"); next_free.clicked.connect(self._select_next_free)
        form.addRow(next_free)

        self.generate_button = QPushButton("GENERAR SERIES")
        self.generate_button.setObjectName("Primary"); self.generate_button.clicked.connect(self.generate_series)
        print_button = QPushButton("IMPRIMIR SERIES GENERADAS")
        print_button.setObjectName("Primary"); print_button.clicked.connect(self.print_a4)
        preview = QPushButton("VISTA PREVIA A4")
        preview.setObjectName("Secondary"); preview.clicked.connect(self.preview_a4)
        save = QPushButton("GUARDAR A4 (SVG)")
        save.setObjectName("Secondary"); save.clicked.connect(self.save_a4)
        form.addRow(self.generate_button); form.addRow(print_button); form.addRow(preview); form.addRow(save)

        advanced_toggle = QToolButton(); advanced_toggle.setText("OPCIONES AVANZADAS")
        advanced_toggle.setCheckable(True); advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        form.addRow(advanced_toggle)
        advanced = QWidget(); advanced_form = QFormLayout(advanced)
        self.empty_color = QLineEdit("#F7DDE7")
        self.accent_color = QLineEdit("#FF4FA3")
        self.secondary_color = QLineEdit("#8FD9FF")
        self.qr = QComboBox(); self.qr.addItem("SIN QR — sin zona reservada", False); self.qr.addItem("CON QR — reservar zona", True); self.qr.setCurrentIndex(1)
        self.duplicate_column = QCheckBox("Repetir la serie a ambos lados del A4")
        self.duplicate_column.setChecked(True)
        self.logo = QLabel("Sin logo seleccionado"); self.logo.setObjectName("Muted"); self.logo.setWordWrap(True)
        logo_button = QPushButton("SELECCIONAR LOGO"); logo_button.setObjectName("Secondary"); logo_button.clicked.connect(self._choose_logo)
        advanced_form.addRow("Color espacios", self.empty_color); advanced_form.addRow("Color principal", self.accent_color)
        advanced_form.addRow("Color secundario", self.secondary_color); advanced_form.addRow("QR", self.qr)
        advanced_form.addRow("A4", self.duplicate_column); advanced_form.addRow(self.logo, logo_button)
        advanced.setVisible(False); advanced_toggle.toggled.connect(advanced.setVisible); form.addRow(advanced)

        info = QLabel(
            "IMPORTANTE: aquí no existe el concepto de reimpresión. Si vuelves a generar el mismo rango, "
            "FB-BINGO recupera la misma serie y los mismos números. Para crear cartones nuevos usa el siguiente rango libre. "
            "Ejemplo: 250 series desde el cartón 1 = cartones 1–1.500; después 250 series desde 1.501 = 1.501–3.000."
        )
        info.setObjectName("Muted"); info.setWordWrap(True); form.addRow(info)
        layout.addWidget(controls)

        preview_panel = QGroupBox("VISTA PREVIA — SERIE DE 6 / A4")
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_widget = QSvgWidget(); self.preview_widget.setMinimumSize(650, 760)
        self.preview_widget.setStyleSheet("background:#FFFFFF;border:1px solid #34405B;border-radius:12px;")
        preview_layout.addWidget(self.preview_widget, 1)
        self.preview_label = QLabel("Elige el inicio y cuántas series deseas generar.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview_label.setObjectName("Muted")
        preview_layout.addWidget(self.preview_label); layout.addWidget(preview_panel, 1)
        self._update_range_label()

    def _normalize_start(self, value: int) -> None:
        normalized = ((value - 1) // 6) * 6 + 1
        if normalized != value:
            self.start_card.blockSignals(True)
            self.start_card.setValue(normalized)
            self.start_card.blockSignals(False)
        self._update_range_label()

    def _select_next_free(self) -> None:
        try:
            count = self.series_count.value() * 6
            self.start_card.setValue(self.production_service.next_generation_start(count))
            self.preview_label.setText("Siguiente bloque libre seleccionado.")
        except ValueError as exc:
            QMessageBox.warning(self, "No hay espacio", str(exc))

    def _update_range_label(self) -> None:
        start = self.start_card.value()
        series = self.series_count.value()
        count = series * 6
        end = start + count - 1
        if end > self.production_service.max_cards:
            self.range_label.setText("Supera la capacidad de 30.000 cartones")
            self.cards_label.setText("—"); self.pages_label.setText("—"); return
        self.range_label.setText(f"{start:,} – {end:,}")
        self.cards_label.setText(f"{count:,} ({series:,} series × 6)")
        self.pages_label.setText(f"{series:,} si la serie se repite a ambos lados")

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path; self.logo.setText(Path(path).name)
            if self._cards: self._render_preview()

    def _style(self) -> PrintStyle:
        return PrintStyle(empty_cell_color=self.empty_color.text().strip() or "#F7DDE7", accent_color=self.accent_color.text().strip() or "#FF4FA3", secondary_accent_color=self.secondary_color.text().strip() or "#8FD9FF", logo_path=self._logo_path, show_model=False, show_serial=True, show_qr_zone=bool(self.qr.currentData()))

    def _requested_range(self) -> tuple[int, int, int]:
        start = self.start_card.value(); count = self.series_count.value() * 6; end = start + count - 1
        if start < 1 or (start - 1) % 6 != 0: raise ValueError("El inicio debe ser 1, 7, 13, 19…; siempre el primer cartón de una serie")
        if end > self.production_service.max_cards: raise ValueError(f"El rango supera la capacidad de {self.production_service.max_cards:,} cartones")
        return start, end, count

    def _load_requested_cards(self, start_card: int, end_card: int) -> None:
        cards = self.repository.get_cards_range(start_card, end_card)
        if len(cards) != end_card - start_card + 1:
            raise ValueError("La generación terminó sin guardar todos los cartones solicitados")
        self._cards = tuple(cards); self._loaded_start_card = start_card; self._loaded_card_count = len(self._cards); self._svg = ""

    def generate_series(self) -> None:
        try:
            start, end, count = self._requested_range(); model = CardModel(self.model.currentData())
            self.generate_button.setEnabled(False); self.generate_button.setText("GENERANDO…")
            self.preview_label.setText(f"Preparando {self.series_count.value():,} series · {count:,} cartones…"); QApplication.processEvents()
            # Un mismo rango es idempotente: si ya existe, se conserva la misma matriz.
            lot = self.production_service.create_lot(start, end, model=model, operator="generador-ui")
            def progress(done: int) -> None:
                self.preview_label.setText(f"Generando… {done:,} / {count:,} cartones"); QApplication.processEvents()
            result = self.production_service.generate_lot(lot.lot_id, progress_callback=progress)
            self._load_requested_cards(start, end); self._render_preview()
            self.preview_label.setText(f"LISTO · {result.series_count:,} series · {result.card_count:,} cartones · {start:,}–{end:,}. Puedes imprimir.")
        except DuplicateProductionError as exc: QMessageBox.warning(self, "Generación detenida", str(exc))
        except (ValueError, RuntimeError, KeyError) as exc: QMessageBox.warning(self, "No se pudo generar", str(exc))
        finally: self.generate_button.setEnabled(True); self.generate_button.setText("GENERAR SERIES")

    def _cards_for_page(self, offset: int) -> tuple[tuple[BingoCard, ...], tuple[BingoCard, ...] | None]:
        if not self._cards: raise ValueError("Primero genera las series")
        left = self._cards[offset:offset + 6]
        if len(left) != 6: raise ValueError("Cada página debe comenzar con una serie completa de 6 cartones")
        if self.duplicate_column.isChecked(): return left, left
        right = self._cards[offset + 6:offset + 12]
        return left, right if len(right) == 6 else None

    def _render_preview(self) -> None:
        left, right = self._cards_for_page(0)
        renderer = A4SvgRenderer(style=self._style())
        self._svg = renderer.render_columns(left, right, duplicate_column=right is left) if right is not None else renderer.render(left)
        self.preview_widget.load(self._svg.encode("utf-8"))

    def preview_a4(self) -> None:
        try:
            start, _, count = self._requested_range()
            if self._loaded_start_card != start or self._loaded_card_count != count: raise ValueError("Primero pulsa GENERAR SERIES para ese rango")
            self._render_preview(); self.preview_label.setText("Vista previa de la primera hoja A4.")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error de vista previa", str(exc))

    def print_a4(self) -> None:
        try:
            start, _, count = self._requested_range()
            if self._loaded_start_card != start or self._loaded_card_count != count: raise ValueError("Primero pulsa GENERAR SERIES para ese rango")
            printer = QPrinter(QPrinter.PrinterMode.HighResolution); printer.setPageSize(QPrinter.PageSize.A4)
            dialog = QPrintDialog(printer, self); dialog.setWindowTitle("Imprimir series FB-BINGO · A4")
            if dialog.exec() != QPrintDialog.DialogCode.Accepted: return
            renderer = A4SvgRenderer(style=self._style()); painter = QPainter(printer); pages = 0
            try:
                step = 6 if self.duplicate_column.isChecked() else 12
                for offset in range(0, count, step):
                    left, right = self._cards_for_page(offset)
                    svg = renderer.render_columns(left, right, duplicate_column=True) if right is left else (renderer.render_columns(left, right) if right is not None else renderer.render(left))
                    svg_renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
                    if not svg_renderer.isValid(): raise RuntimeError(f"No se pudo preparar la hoja que comienza en {start + offset:,}")
                    if pages and not printer.newPage(): raise RuntimeError("La impresora no pudo crear una nueva página A4")
                    svg_renderer.render(painter); pages += 1
            finally: painter.end()
            self.preview_label.setText(f"IMPRESIÓN COMPLETADA · {pages:,} hojas A4 · {count:,} cartones. La próxima generación usa el siguiente rango libre.")
        except (ValueError, OSError, RuntimeError, KeyError) as exc: QMessageBox.warning(self, "Error de impresión", str(exc))

    def save_a4(self) -> None:
        try:
            start, _, count = self._requested_range()
            if self._loaded_start_card != start or self._loaded_card_count != count: raise ValueError("Primero genera las series")
            if not self._svg: self._render_preview()
            path, _ = QFileDialog.getSaveFileName(self, "Guardar primera hoja A4", f"fb_bingo_series_{start}-{start + 5}.svg", "SVG (*.svg)")
            if path: Path(path).write_text(self._svg, encoding="utf-8")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error al guardar", str(exc))


GeneratorWindow = GeneratorWidget
