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

from app.cards import BingoCard, CardModel
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import DuplicateProductionError, ProductionService
from app.settings.paths import database_path


class GeneratorWidget(QWidget):
    """Generador e impresor A4 masivo con reimpresión libre."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None, max_cards: int = 30_000) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(database_path())
        self.production_service = ProductionService(self.repository, max_cards=max_cards)
        self._series = None
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

        controls = QGroupBox("IMPRESOR DE CARTONES")
        controls.setMinimumWidth(390)
        form = QFormLayout(controls)

        self.model = QComboBox()
        self.model.addItem("Modelo A · PRINCIPAL", CardModel.A.value)
        self.model.addItem("Modelo B · ESPECIAL", CardModel.B.value)

        self.start_card = QSpinBox()
        self.start_card.setRange(1, self.production_service.max_cards)
        self.start_card.setValue(1)

        self.card_count = QSpinBox()
        self.card_count.setRange(6, self.production_service.max_cards)
        self.card_count.setSingleStep(6)
        self.card_count.setValue(6)

        self.range_label = QLabel()
        self.range_label.setObjectName("Muted")
        self.series_count_label = QLabel()
        self.series_count_label.setObjectName("Muted")
        self.pages_label = QLabel()
        self.pages_label.setObjectName("Muted")
        self.start_card.valueChanged.connect(self._update_range_label)
        self.card_count.valueChanged.connect(self._update_range_label)

        form.addRow("Modelo", self.model)
        form.addRow("Seguir desde cartón Nº", self.start_card)
        form.addRow("Cantidad de cartones", self.card_count)
        form.addRow("Rango", self.range_label)
        form.addRow("Series de 6", self.series_count_label)
        form.addRow("Hojas A4", self.pages_label)

        generate = QPushButton("GENERAR / CARGAR")
        generate.setObjectName("Primary")
        generate.clicked.connect(self.generate_series)
        print_button = QPushButton("IMPRIMIR CARTONES")
        print_button.setObjectName("Primary")
        print_button.clicked.connect(self.print_a4)
        reprint_button = QPushButton("REIMPRIMIR")
        reprint_button.setObjectName("Secondary")
        reprint_button.clicked.connect(self.print_a4)
        preview = QPushButton("VISTA PREVIA A4")
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
        self.duplicate_column = QCheckBox("Duplicar cada serie en ambos lados")
        self.duplicate_column.setChecked(False)
        self.duplicate_column.toggled.connect(self._update_range_label)
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
            "Puedes empezar desde cualquier cartón (1, 2, 3, 1501, etc.). "
            "La cantidad se agrupa en bloques de 6 para impresión. Si esos cartones ya fueron generados, "
            "FB-BINGO los carga exactamente iguales y permite imprimirlos de nuevo sin avisos de duplicado. "
            "DUPLICAR repite físicamente la misma serie 1–6 en ambos lados de la hoja."
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
        self.preview_label = QLabel("Ingresa el cartón inicial y la cantidad.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("Muted")
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_panel, 1)
        self._update_range_label()

    def _update_range_label(self) -> None:
        start = self.start_card.value()
        count = self.card_count.value()
        end = start + count - 1
        if end > self.production_service.max_cards:
            self.range_label.setText("Supera la capacidad configurada")
            self.series_count_label.setText("—")
            self.pages_label.setText("—")
            return
        if count % 6 != 0:
            self.range_label.setText(f"{start:,} – {end:,}")
            self.series_count_label.setText("Cantidad debe ser múltiplo de 6")
            self.pages_label.setText("—")
            return
        series = count // 6
        duplicate = hasattr(self, "duplicate_column") and self.duplicate_column.isChecked()
        pages = series if duplicate else (series + 1) // 2
        self.range_label.setText(f"{start:,} – {end:,} ({count:,} cartones)")
        self.series_count_label.setText(f"{series:,}")
        self.pages_label.setText(f"{pages:,}")

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path
            self.logo.setText(Path(path).name)
            if self._cards:
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
        if end_card > self.production_service.max_cards:
            raise ValueError(f"El rango supera la capacidad configurada de {self.production_service.max_cards:,} cartones")
        if card_count % 6 != 0:
            raise ValueError("La cantidad de cartones debe ser múltiplo de 6")
        return start_card, end_card, card_count

    def _load_requested_cards(self, start_card: int, end_card: int) -> None:
        self._cards = self.repository.get_cards_range(start_card, end_card)
        self._loaded_start_card = start_card
        self._loaded_card_count = end_card - start_card + 1
        self._svg = ""

    def generate_series(self) -> None:
        model = CardModel(self.model.currentData())
        try:
            start_card, end_card, card_count = self._requested_range()
            lot = self.production_service.create_lot(start_card, end_card, model=model, operator="generador-ui")
            result = self.production_service.generate_lot(lot.lot_id)
            self._load_requested_cards(start_card, end_card)
            self._render_preview()
            self.preview_label.setText(
                f"LISTO · {result.card_count:,} cartones · {result.series_count:,} series de 6 · "
                f"rango {start_card:,}–{end_card:,}. Puede imprimir o reimprimir sin límite."
            )
        except DuplicateProductionError as exc:
            QMessageBox.warning(self, "No se pudo cargar la producción", str(exc))
        except (ValueError, RuntimeError, KeyError) as exc:
            QMessageBox.warning(self, "No se pudo generar", str(exc))

    def _cards_for_page(self, offset: int) -> tuple[tuple[BingoCard, ...], tuple[BingoCard, ...] | None]:
        if not self._cards:
            raise ValueError("No hay cartones cargados")
        left = self._cards[offset : offset + 6]
        if len(left) != 6:
            raise ValueError("La producción no contiene una serie completa de 6 cartones")
        if self.duplicate_column.isChecked():
            return left, left
        right = self._cards[offset + 6 : offset + 12]
        return left, right if len(right) == 6 else None

    def _render_preview(self) -> None:
        if len(self._cards) < 6:
            raise ValueError("No hay una serie completa cargada")
        renderer = A4SvgRenderer(style=self._style())
        left, right = self._cards_for_page(0)
        self._svg = renderer.render_columns(left, right, duplicate_column=right is left) if right is not None else renderer.render(left)
        self.preview_widget.load(self._svg.encode("utf-8"))
        self._update_range_label()

    def preview_a4(self) -> None:
        try:
            start_card, end_card, card_count = self._requested_range()
            if self._loaded_start_card != start_card or self._loaded_card_count != card_count:
                self.generate_series()
                return
            self._render_preview()
            self.preview_label.setText("Vista A4 · 12 posiciones · la primera hoja de la producción")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error de vista previa", str(exc))

    def print_a4(self) -> None:
        try:
            start_card, end_card, card_count = self._requested_range()
            if self._loaded_start_card != start_card or self._loaded_card_count != card_count:
                self.generate_series()
            if len(self._cards) != card_count:
                raise ValueError("No se pudieron cargar todos los cartones solicitados")

            printer = QPrinter(QPrinter.PrinterMode.HighResolution)
            printer.setPageSize(QPrinter.PageSize.A4)
            dialog = QPrintDialog(printer, self)
            dialog.setWindowTitle("Imprimir cartones FB-BINGO · A4")
            if dialog.exec() != QPrintDialog.DialogCode.Accepted:
                return

            renderer = A4SvgRenderer(style=self._style())
            painter = QPainter(printer)
            pages = 0
            try:
                step = 6 if self.duplicate_column.isChecked() else 12
                for offset in range(0, card_count, step):
                    left, right = self._cards_for_page(offset)
                    svg = renderer.render_columns(left, right, duplicate_column=True) if right is left else (
                        renderer.render_columns(left, right) if right is not None else renderer.render(left)
                    )
                    svg_renderer = QSvgRenderer(QByteArray(svg.encode("utf-8")))
                    if not svg_renderer.isValid():
                        raise RuntimeError(f"No se pudo preparar la hoja A4 que comienza en el cartón {start_card + offset:,}")
                    if pages and not printer.newPage():
                        raise RuntimeError("La impresora no pudo crear una nueva página A4")
                    svg_renderer.render(painter)
                    pages += 1
            finally:
                painter.end()

            physical_cards = card_count * (2 if self.duplicate_column.isChecked() else 1)
            self.preview_label.setText(
                f"IMPRESIÓN COMPLETADA · {pages:,} hojas A4 · {physical_cards:,} cartones físicos. "
                "Puedes volver a imprimir exactamente el mismo rango cuando quieras."
            )
        except (ValueError, OSError, RuntimeError, KeyError) as exc:
            QMessageBox.warning(self, "Error de impresión", str(exc))

    def save_a4(self) -> None:
        try:
            if not self._cards:
                self.generate_series()
            if not self._cards:
                raise ValueError("No hay cartones cargados")
            if not self._svg:
                self._render_preview()
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar hoja A4",
                f"fb_bingo_cartones_{self.start_card.value()}-{self.start_card.value() + 5}.svg",
                "SVG (*.svg)",
            )
            if path:
                Path(path).write_text(self._svg, encoding="utf-8")
                QMessageBox.information(self, "A4 guardado", "La hoja A4 fue guardada correctamente.")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error al guardar", str(exc))


GeneratorWindow = GeneratorWidget
