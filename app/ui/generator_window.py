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
    """Producción y impresión separadas: generar crea series; imprimir solo lee."""

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

        controls = QGroupBox("PRODUCCIÓN E IMPRESIÓN")
        controls.setMinimumWidth(470)
        form = QFormLayout(controls)

        self.model = QComboBox()
        self.model.addItem("Modelo A · PRINCIPAL", CardModel.A.value)
        self.model.addItem("Modelo B · ESPECIAL", CardModel.B.value)

        # GENERACIÓN: siempre empieza en 1, 7, 13… y genera series completas.
        generation_box = QGroupBox("GENERAR CARTONES NUEVOS")
        generation_form = QFormLayout(generation_box)
        self.start_card = QSpinBox()
        self.start_card.setRange(1, self.production_service.max_cards - 5)
        self.start_card.setSingleStep(6)
        self.start_card.setValue(1)
        self.start_card.valueChanged.connect(self._normalize_generation_start)
        self.series_count = QSpinBox()
        self.series_count.setRange(1, self.production_service.max_cards // 6)
        self.series_count.setValue(1)
        self.series_count.valueChanged.connect(self._update_generation_labels)
        self.generation_range_label = QLabel(); self.generation_range_label.setObjectName("Muted")
        self.generation_cards_label = QLabel(); self.generation_cards_label.setObjectName("Muted")
        generation_form.addRow("Primera serie desde cartón", self.start_card)
        generation_form.addRow("Cantidad de series", self.series_count)
        generation_form.addRow("Rango nuevo", self.generation_range_label)
        generation_form.addRow("Cantidad", self.generation_cards_label)
        next_free = QPushButton("PRÓXIMO BLOQUE LIBRE")
        next_free.setObjectName("Secondary"); next_free.clicked.connect(self._select_next_free)
        generation_form.addRow(next_free)
        self.generate_button = QPushButton("GENERAR SERIES")
        self.generate_button.setObjectName("Primary"); self.generate_button.clicked.connect(self.generate_series)
        generation_form.addRow(self.generate_button)
        form.addRow(generation_box)

        # IMPRESIÓN: puede comenzar en cualquier cartón existente, incluido 2.
        print_box = QGroupBox("IMPRIMIR CARTONES EXISTENTES")
        print_form = QFormLayout(print_box)
        self.print_start_card = QSpinBox(); self.print_start_card.setRange(1, self.production_service.max_cards); self.print_start_card.setValue(1)
        self.print_count = QSpinBox(); self.print_count.setRange(1, self.production_service.max_cards); self.print_count.setValue(6)
        self.print_count.valueChanged.connect(self._update_print_labels)
        self.print_end_label = QLabel(); self.print_end_label.setObjectName("Muted")
        self.print_found_label = QLabel(); self.print_found_label.setObjectName("Muted")
        print_form.addRow("Desde cartón", self.print_start_card)
        print_form.addRow("Cantidad de cartones", self.print_count)
        print_form.addRow("Hasta cartón", self.print_end_label)
        print_form.addRow("Disponibles", self.print_found_label)
        self.print_button = QPushButton("IMPRIMIR CARTONES")
        self.print_button.setObjectName("Primary"); self.print_button.clicked.connect(self.print_existing_cards)
        preview_print = QPushButton("VISTA PREVIA DE IMPRESIÓN")
        preview_print.setObjectName("Secondary"); preview_print.clicked.connect(self.preview_existing_cards)
        print_form.addRow(self.print_button); print_form.addRow(preview_print)
        form.addRow(print_box)
        self.print_start_card.valueChanged.connect(self._update_print_labels)

        self.model.currentIndexChanged.connect(self._invalidate_generation_preview)

        advanced_toggle = QToolButton(); advanced_toggle.setText("OPCIONES DE DISEÑO")
        advanced_toggle.setCheckable(True); advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        form.addRow(advanced_toggle)
        advanced = QWidget(); advanced_form = QFormLayout(advanced)
        self.empty_color = QLineEdit("#F7DDE7")
        self.accent_color = QLineEdit("#FF4FA3")
        self.secondary_color = QLineEdit("#8FD9FF")
        self.qr = QComboBox(); self.qr.addItem("SIN QR — sin zona reservada", False); self.qr.addItem("CON QR — reservar zona", True); self.qr.setCurrentIndex(1)
        self.duplicate_column = QCheckBox("Repetir los 6 cartones en la segunda columna A4")
        self.duplicate_column.setChecked(True)
        self.logo = QLabel("Sin logo seleccionado"); self.logo.setObjectName("Muted"); self.logo.setWordWrap(True)
        logo_button = QPushButton("SELECCIONAR LOGO"); logo_button.setObjectName("Secondary"); logo_button.clicked.connect(self._choose_logo)
        advanced_form.addRow("Espacios", self.empty_color); advanced_form.addRow("Rosa palo", self.accent_color)
        advanced_form.addRow("Celeste", self.secondary_color); advanced_form.addRow("QR", self.qr)
        advanced_form.addRow("A4", self.duplicate_column); advanced_form.addRow(self.logo, logo_button)
        advanced.setVisible(False); advanced_toggle.toggled.connect(advanced.setVisible); form.addRow(advanced)

        info = QLabel(
            "REGLA FIJA: generar crea bloques 1–6, 7–12, 13–18… y cada bloque cubre 1–90 una vez. "
            "IMPRIMIR no genera ni modifica nada: puedes imprimir desde el cartón 2, 3, 7, etc. y se leen exactamente los cartones guardados."
        )
        info.setObjectName("Muted"); info.setWordWrap(True); form.addRow(info)
        layout.addWidget(controls)

        preview_panel = QGroupBox("VISTA REAL DEL CARTÓN / A4")
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_widget = QSvgWidget(); self.preview_widget.setMinimumSize(650, 760)
        self.preview_widget.setStyleSheet("background:#FFFFFF;border:1px solid #34405B;border-radius:12px;")
        preview_layout.addWidget(self.preview_widget, 1)
        self.preview_label = QLabel("Genera una serie o selecciona cartones existentes para visualizar la impresión.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter); self.preview_label.setObjectName("Muted")
        preview_layout.addWidget(self.preview_label); layout.addWidget(preview_panel, 1)
        self._update_generation_labels(); self._update_print_labels()

    def _normalize_generation_start(self, value: int) -> None:
        normalized = ((value - 1) // 6) * 6 + 1
        if normalized != value:
            self.start_card.blockSignals(True); self.start_card.setValue(normalized); self.start_card.blockSignals(False)
        self._update_generation_labels()

    def _select_next_free(self) -> None:
        try:
            count = self.series_count.value() * 6
            self.start_card.setValue(self.production_service.next_generation_start(count))
            self.preview_label.setText("Siguiente bloque libre seleccionado.")
        except ValueError as exc:
            QMessageBox.warning(self, "No hay espacio", str(exc))

    def _update_generation_labels(self) -> None:
        start = self.start_card.value(); count = self.series_count.value() * 6; end = start + count - 1
        if end > self.production_service.max_cards:
            self.generation_range_label.setText("Supera la capacidad"); self.generation_cards_label.setText("—"); return
        self.generation_range_label.setText(f"{start:,} – {end:,}")
        self.generation_cards_label.setText(f"{count:,} ({self.series_count.value():,} series × 6)")

    def _update_print_labels(self) -> None:
        start = self.print_start_card.value(); count = self.print_count.value(); end = start + count - 1
        if end > self.production_service.max_cards:
            self.print_end_label.setText("Supera 30.000"); self.print_found_label.setText("—"); return
        self.print_end_label.setText(f"{end:,}")
        try:
            found = len(self.repository.get_cards_range(start, end))
            self.print_found_label.setText(f"{found:,} de {count:,}")
        except (OSError, ValueError):
            self.print_found_label.setText("—")

    def _invalidate_generation_preview(self) -> None:
        self._cards = (); self._loaded_start_card = None; self._loaded_card_count = None; self._svg = ""

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path; self.logo.setText(Path(path).name)
            if self._cards: self._render_cards(self._cards[:6])

    def _style(self) -> PrintStyle:
        return PrintStyle(empty_cell_color=self.empty_color.text().strip() or "#F7DDE7", accent_color=self.accent_color.text().strip() or "#FF4FA3", secondary_accent_color=self.secondary_color.text().strip() or "#8FD9FF", logo_path=self._logo_path, show_model=False, show_serial=True, show_qr_zone=bool(self.qr.currentData()))

    def _generation_range(self) -> tuple[int, int, int]:
        start = self.start_card.value(); count = self.series_count.value() * 6; end = start + count - 1
        if (start - 1) % 6 != 0:
            raise ValueError("La generación debe comenzar en 1, 7, 13, 19…")
        if end > self.production_service.max_cards:
            raise ValueError(f"El rango supera la capacidad de {self.production_service.max_cards:,} cartones")
        return start, end, count

    def _print_range(self) -> tuple[int, int, int]:
        start = self.print_start_card.value(); count = self.print_count.value(); end = start + count - 1
        if end > self.production_service.max_cards:
            raise ValueError(f"El rango supera la capacidad de {self.production_service.max_cards:,} cartones")
        return start, end, count

    def _load_cards(self, start_card: int, end_card: int) -> tuple[BingoCard, ...]:
        cards = tuple(self.repository.get_cards_range(start_card, end_card))
        if len(cards) != end_card - start_card + 1:
            raise ValueError(f"No existen todos los cartones del rango {start_card:,}–{end_card:,}. Primero genera ese bloque.")
        return cards

    def generate_series(self) -> None:
        try:
            start, end, count = self._generation_range(); model = CardModel(self.model.currentData())
            self.generate_button.setEnabled(False); self.generate_button.setText("GENERANDO…")
            self.preview_label.setText(f"Preparando {self.series_count.value():,} series · {count:,} cartones…"); QApplication.processEvents()
            lot = self.production_service.create_lot(start, end, model=model, operator="generador-ui")
            def progress(done: int) -> None:
                self.preview_label.setText(f"Generando… {done:,} / {count:,} cartones"); QApplication.processEvents()
            result = self.production_service.generate_lot(lot.lot_id, progress_callback=progress)
            self._cards = self._load_cards(start, end); self._loaded_start_card = start; self._loaded_card_count = count
            self._render_cards(self._cards[:6])
            self.preview_label.setText(f"LISTO · {result.series_count:,} series · {result.card_count:,} cartones · {start:,}–{end:,}. Ahora puedes imprimir cualquier rango existente.")
            self._update_print_labels()
        except DuplicateProductionError as exc: QMessageBox.warning(self, "Generación detenida", str(exc))
        except (ValueError, RuntimeError, KeyError) as exc: QMessageBox.warning(self, "No se pudo generar", str(exc))
        finally: self.generate_button.setEnabled(True); self.generate_button.setText("GENERAR SERIES")

    def _render_cards(self, cards: tuple[BingoCard, ...]) -> None:
        if len(cards) != 6:
            raise ValueError("La vista A4 necesita 6 cartones")
        renderer = A4SvgRenderer(style=self._style())
        self._svg = renderer.render_columns(cards, cards, duplicate_column=True)
        self.preview_widget.load(self._svg.encode("utf-8"))

    def _page_cards(self, cards: tuple[BingoCard, ...], offset: int) -> tuple[tuple[BingoCard, ...], tuple[BingoCard, ...] | None]:
        left = cards[offset:offset + 6]
        if len(left) != 6:
            raise ValueError("El rango debe contener una cantidad múltiplo de 6 para completar hojas A4")
        if self.duplicate_column.isChecked():
            return left, left
        right = cards[offset + 6:offset + 12]
        return left, right if len(right) == 6 else None

    def _render_page(self, left: tuple[BingoCard, ...], right: tuple[BingoCard, ...] | None) -> str:
        renderer = A4SvgRenderer(style=self._style())
        return renderer.render_columns(left, right, duplicate_column=right is left) if right is not None else renderer.render(left)

    def preview_existing_cards(self) -> None:
        try:
            start, end, count = self._print_range()
            cards = self._load_cards(start, end)
            if count % 6:
                raise ValueError("Para la impresión A4 la cantidad debe ser múltiplo de 6 cartones")
            left, right = self._page_cards(cards, 0)
            self._svg = self._render_page(left, right); self.preview_widget.load(self._svg.encode("utf-8"))
            self.preview_label.setText(f"VISTA REAL · cartones {start:,}–{end:,}. No se generó ningún cartón.")
        except (ValueError, OSError, RuntimeError) as exc: QMessageBox.warning(self, "Vista previa", str(exc))

    def print_existing_cards(self) -> None:
        try:
            start, end, count = self._print_range()
            if count % 6:
                raise ValueError("Para la impresión A4 la cantidad debe ser múltiplo de 6 cartones")
            cards = self._load_cards(start, end)
            printer = QPrinter(QPrinter.PrinterMode.HighResolution); printer.setPageSize(QPrinter.PageSize.A4)
            dialog = QPrintDialog(printer, self); dialog.setWindowTitle("Imprimir cartones FB-BINGO · A4")
            if dialog.exec() != QPrintDialog.DialogCode.Accepted: return
            painter = QPainter(printer); renderer = A4SvgRenderer(style=self._style()); pages = 0
            try:
                step = 6 if self.duplicate_column.isChecked() else 12
                for offset in range(0, count, step):
                    left, right = self._page_cards(cards, offset)
                    svg = self._render_page(left, right)
                    svg_renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
                    if not svg_renderer.isValid(): raise RuntimeError(f"No se pudo preparar la hoja que comienza en {start + offset:,}")
                    if pages and not printer.newPage(): raise RuntimeError("La impresora no pudo crear una nueva página A4")
                    svg_renderer.render(painter); pages += 1
            finally: painter.end()
            self.preview_label.setText(f"IMPRESIÓN COMPLETADA · {pages:,} hojas A4 · cartones {start:,}–{end:,}. Sin regenerar.")
        except (ValueError, OSError, RuntimeError) as exc: QMessageBox.warning(self, "Error de impresión", str(exc))

    # Compatibilidad con llamadas existentes: ahora imprimir siempre significa
    # imprimir cartones ya guardados, nunca volver a generarlos.
    def print_a4(self) -> None:
        self.print_existing_cards()

    def preview_a4(self) -> None:
        self.preview_existing_cards()

    def save_a4(self) -> None:
        try:
            if not self._svg: self.preview_existing_cards()
            if not self._svg: return
            start = self.print_start_card.value(); end = start + self.print_count.value() - 1
            path, _ = QFileDialog.getSaveFileName(self, "Guardar primera hoja A4", f"fb_bingo_cartones_{start}-{end}.svg", "SVG (*.svg)")
            if path: Path(path).write_text(self._svg, encoding="utf-8")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error al guardar", str(exc))


GeneratorWindow = GeneratorWidget
