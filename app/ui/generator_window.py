from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QByteArray, Qt
from PySide6.QtGui import QPainter
from PySide6.QtPrintSupport import QPrintDialog, QPrinter
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.printing.batches import iter_a4_series_batches
from app.production import DuplicateProductionError, ProductionService
from app.settings.paths import database_path


class GeneratorWidget(QWidget):
    """Generador y productor de cartones con impresión A4 masiva y reimpresión libre."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None, max_cards: int = 30_000) -> None:
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
        controls.setMinimumWidth(390)
        form = QFormLayout(controls)

        self.model = QComboBox()
        self.model.addItem("Modelo A · PRINCIPAL", CardModel.A.value)
        self.model.addItem("Modelo B · ESPECIAL", CardModel.B.value)

        self.start_card = QSpinBox()
        self.start_card.setRange(1, self.production_service.max_cards)
        self.start_card.setSingleStep(6)
        self.start_card.setValue(1)

        self.card_count = QSpinBox()
        self.card_count.setRange(6, self.production_service.max_cards)
        self.card_count.setSingleStep(6)
        self.card_count.setValue(6)

        self.series_count_label = QLabel()
        self.series_count_label.setObjectName("Muted")
        self.range_label = QLabel()
        self.range_label.setObjectName("Muted")
        self._update_range_label()
        self.start_card.valueChanged.connect(self._update_range_label)
        self.card_count.valueChanged.connect(self._update_range_label)

        form.addRow("Modelo", self.model)
        form.addRow("Cartón inicial", self.start_card)
        form.addRow("Cantidad de cartones", self.card_count)
        form.addRow("Producción", self.range_label)
        form.addRow("Series", self.series_count_label)

        generate = QPushButton("GENERAR / CARGAR")
        generate.setObjectName("Primary")
        generate.clicked.connect(self.generate_series)
        print_button = QPushButton("IMPRIMIR PRODUCCIÓN A4")
        print_button.setObjectName("Primary")
        print_button.clicked.connect(self.print_a4)
        reprint_button = QPushButton("REIMPRIMIR PRODUCCIÓN A4")
        reprint_button.setObjectName("Secondary")
        reprint_button.clicked.connect(self.print_a4)
        preview = QPushButton("ACTUALIZAR VISTA A4")
        preview.setObjectName("Secondary")
        preview.clicked.connect(self.preview_a4)
        save = QPushButton("GUARDAR A4 (SVG)")
        save.setObjectName("Secondary")
        save.clicked.connect(self.save_a4)

        form.addRow(generate)
        form.addRow(print_button)
        form.addRow(reprint_button)
        form.addRow(preview)
        form.addRow(save)

        advanced_toggle = QToolButton()
        advanced_toggle.setText("OPCIONES AVANZADAS")
        advanced_toggle.setCheckable(True)
        advanced_toggle.setChecked(False)
        advanced_toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextOnly)
        form.addRow(advanced_toggle)

        advanced = QWidget()
        advanced_form = QFormLayout(advanced)
        self.empty_color = QLineEdit("#F7DDE7")
        self.accent_color = QLineEdit("#FF4FA3")
        self.secondary_color = QLineEdit("#8FD9FF")
        self.qr = QComboBox()
        self.qr.addItem("SIN QR — sin zona reservada", False)
        self.qr.addItem("CON QR — reservar zona", True)
        self.duplicate_column = QCheckBox("Duplicar la serie 1–6 en ambos lados")
        self.duplicate_column.setChecked(False)
        self.logo = QLabel("Sin logo seleccionado")
        self.logo.setObjectName("Muted")
        self.logo.setWordWrap(True)
        logo_button = QPushButton("SELECCIONAR LOGO")
        logo_button.setObjectName("Secondary")
        logo_button.clicked.connect(self._choose_logo)
        advanced_form.addRow("Color espacios", self.empty_color)
        advanced_form.addRow("Color principal", self.accent_color)
        advanced_form.addRow("Color secundario", self.secondary_color)
        advanced_form.addRow("QR", self.qr)
        advanced_form.addRow("Impresión", self.duplicate_column)
        advanced_form.addRow(self.logo, logo_button)
        advanced.setVisible(False)
        advanced_toggle.toggled.connect(advanced.setVisible)
        form.addRow(advanced)

        info = QLabel(
            "Cada serie tiene 6 cartones. Si el rango ya existe, FB-BINGO reutiliza exactamente los mismos cartones para imprimirlos otra vez; no los regenera. "
            "La cantidad se expresa en cartones y el programa calcula automáticamente las series."
        )
        info.setObjectName("Muted")
        info.setWordWrap(True)
        form.addRow(info)
        layout.addWidget(controls)

        preview_panel = QGroupBox("VISTA PREVIA — A4 / 12 POSICIONES")
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_widget = QSvgWidget()
        self.preview_widget.setMinimumSize(650, 760)
        self.preview_widget.setStyleSheet("background:#FFFFFF;border:1px solid #34405B;border-radius:12px;")
        preview_layout.addWidget(self.preview_widget, 1)
        self.preview_label = QLabel("Ingresa la cantidad de cartones y pulsa GENERAR / CARGAR.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("Muted")
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_panel, 1)

    def _update_range_label(self) -> None:
        start = self.start_card.value()
        count = self.card_count.value()
        end = start + count - 1
        if end > self.production_service.max_cards:
            self.range_label.setText("El rango supera la capacidad configurada")
            self.series_count_label.setText("—")
            return
        if (start - 1) % 6 != 0 or count % 6 != 0:
            self.range_label.setText(f"{start:,} – {end:,} · debe comenzar y terminar en series completas")
            self.series_count_label.setText("—")
            return
        self.range_label.setText(f"{start:,} – {end:,} ({count:,} cartones)")
        self.series_count_label.setText(f"{count // 6:,}")

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path
            self.logo.setText(Path(path).name)
            if self._series is not None:
                self._render_preview()

    def _style(self) -> PrintStyle:
        return PrintStyle(
            empty_cell_color=self.empty_color.text().strip() or "#F7DDE7",
            accent_color=self.accent_color.text().strip() or "#FF4FA3",
            secondary_accent_color=self.secondary_color.text().strip() or "#8FD9FF",
            logo_path=self._logo_path,
            show_model=False,
            show_serial=True,
            show_qr_zone=bool(self.qr.currentData()),
        )

    def _requested_range(self) -> tuple[int, int, int]:
        start_card = self.start_card.value()
        card_count = self.card_count.value()
        end_card = start_card + card_count - 1
        if (start_card - 1) % 6 != 0 or card_count % 6 != 0:
            raise ValueError("La producción debe comenzar en el primer cartón de una serie y contener series completas de 6 cartones")
        if end_card > self.production_service.max_cards:
            raise ValueError(f"El rango supera la capacidad configurada de {self.production_service.max_cards:,} cartones")
        first_series = (start_card - 1) // 6 + 1
        return first_series, start_card, end_card

    def _load_requested_series(self, first_series: int) -> None:
        self._series = self.repository.get(f"{first_series:04d}")

    def generate_series(self) -> None:
        model = CardModel(self.model.currentData())
        try:
            first_series, start_card, end_card = self._requested_range()
            lot = self.production_service.create_lot(
                start_card,
                end_card,
                model=model,
                operator="generador-ui",
            )
            result = self.production_service.generate_lot(lot.lot_id)
            self._load_requested_series(first_series)
            self._render_preview()
            self.preview_label.setText(
                f"LISTO · {result.series_count:,} serie(s) · {result.card_count:,} cartones · "
                f"series {first_series:04d}–{first_series + result.series_count - 1:04d}. "
                "Los cartones pueden imprimirse nuevamente cuando quieras."
            )
        except DuplicateProductionError as exc:
            QMessageBox.warning(self, "No se pudo cargar la producción", str(exc))
        except (ValueError, RuntimeError, KeyError) as exc:
            QMessageBox.warning(self, "No se pudo generar", str(exc))

    def _series_by_number(self, series_number: int):
        return self.repository.get(f"{series_number:04d}")

    def _next_series(self):
        if self._series is None:
            return None
        try:
            return self._series_by_number(int(self._series.series_id) + 1)
        except KeyError:
            return None

    def _render_preview(self) -> None:
        if self._series is None:
            raise ValueError("No hay una serie cargada")
        renderer = A4SvgRenderer(style=self._style())
        right = self._series.cards if self.duplicate_column.isChecked() else (self._next_series().cards if self._next_series() is not None else None)
        self._svg = renderer.render_columns(
            self._series.cards,
            right,
            duplicate_column=self.duplicate_column.isChecked(),
        ) if right is not None else renderer.render(self._series.cards)
        self.preview_widget.load(self._svg.encode("utf-8"))

    def preview_a4(self) -> None:
        try:
            if self._series is None:
                self.generate_series()
                return
            self._render_preview()
            first_series = int(self._series.series_id)
            derecha = f"{first_series:04d}" if self.duplicate_column.isChecked() else f"{first_series + 1:04d}"
            self.preview_label.setText(f"Vista A4 · izquierda {first_series:04d} · derecha {derecha}")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error de vista previa", str(exc))

    def _print_page(self, printer: QPrinter, left_series_number: int, right_series_number: int | None, renderer: A4SvgRenderer, painter: QPainter) -> None:
        left = self._series_by_number(left_series_number)
        if right_series_number is None:
            svg = renderer.render(left.cards)
        else:
            right = self._series_by_number(right_series_number)
            svg = renderer.render_columns(left.cards, right.cards, duplicate_column=left_series_number == right_series_number)
        svg_renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
        if not svg_renderer.isValid():
            raise RuntimeError(f"No se pudo preparar la hoja A4 de la serie {left_series_number:04d}")
        svg_renderer.render(painter)

    def print_a4(self) -> None:
        try:
            first_series, _, _ = self._requested_range()
            series_count = self.card_count.value() // 6
            if self._series is None or int(self._series.series_id) != first_series:
                self.generate_series()
            if self._series is None:
                raise ValueError("No hay una producción cargada")

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPrinter.PageSize.A4)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir producción FB-BINGO · A4")
            if dialog.exec() != QPrintDialog.DialogCode.Accepted:
                return

            renderer = A4SvgRenderer(style=self._style())
            painter = QPainter(printer)
            pages = 0
            try:
                for left_series, right_series in iter_a4_series_batches(
                    first_series,
                    series_count,
                    duplicate=self.duplicate_column.isChecked(),
                ):
                    if pages:
                        if not printer.newPage():
                            raise RuntimeError("La impresora no pudo crear una nueva página A4")
                    self._print_page(printer, left_series, right_series, renderer, painter)
                    pages += 1
            finally:
                painter.end()

            self.preview_label.setText(
                f"IMPRESIÓN COMPLETADA · {pages:,} hojas A4 · {self.card_count.value():,} cartones. "
                "Puede volver a imprimir esta producción cuando quiera."
            )
        except (ValueError, OSError, RuntimeError, KeyError) as exc:
            QMessageBox.warning(self, "Error de impresión", str(exc))

    def save_a4(self) -> None:
        try:
            if self._series is None:
                self.generate_series()
            if self._series is None:
                raise ValueError("No hay una serie cargada")
            if not self._svg:
                self._render_preview()
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar hoja A4",
                f"fb_bingo_serie_{self._series.series_id}.svg",
                "SVG (*.svg)",
            )
            if path:
                Path(path).write_text(self._svg, encoding="utf-8")
                QMessageBox.information(self, "A4 guardado", "La hoja A4 fue guardada correctamente.")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error al guardar", str(exc))


GeneratorWindow = GeneratorWidget
