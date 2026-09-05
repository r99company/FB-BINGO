from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
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
    QVBoxLayout,
    QWidget,
)

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.settings.paths import database_path


class GeneratorWidget(QWidget):
    """Generator UI embeddable as a tab in the main application."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(database_path())
        self._series = None
        self._logo_path: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        controls = QGroupBox("Generador de Cartones")
        form = QFormLayout(controls)
        self.model = QComboBox(); self.model.addItems(["Modelo A", "Modelo B"])
        self.series_id = QSpinBox(); self.series_id.setRange(1, 2_500); self.series_id.setValue(1)
        self.quantity = QSpinBox(); self.quantity.setRange(1, 2_500); self.quantity.setValue(1)
        self.serial_start = QSpinBox(); self.serial_start.setRange(1, 30_000); self.serial_start.setValue(1)
        self.empty_color = QLineEdit("#F7DDE7")
        self.accent_color = QLineEdit("#9ED8EA")
        self.logo = QLabel("Sin logo"); self.logo.setWordWrap(True)
        logo_button = QPushButton("Seleccionar logo"); logo_button.clicked.connect(self._choose_logo)
        generate = QPushButton("GENERAR SERIES"); generate.clicked.connect(self.generate_series)
        preview = QPushButton("VISTA PREVIA A4"); preview.clicked.connect(self.preview_a4)
        save = QPushButton("GUARDAR A4 SVG"); save.clicked.connect(self.save_a4)
        for label, widget in (("Modelo:", self.model), ("Serie inicial:", self.series_id),
                              ("Cantidad de series:", self.quantity), ("Serial inicial:", self.serial_start),
                              ("Color espacios vacíos:", self.empty_color), ("Color acento:", self.accent_color)):
            form.addRow(label, widget)
        form.addRow(self.logo, logo_button); form.addRow(generate); form.addRow(preview); form.addRow(save)
        layout.addWidget(controls)
        self.preview_label = QLabel("Configura y genera una serie.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #9ED8EA; padding: 20px;")
        layout.addWidget(self.preview_label, 1)

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path: self._logo_path = path; self.logo.setText(Path(path).name)

    def _style(self) -> PrintStyle:
        return PrintStyle(empty_cell_color=self.empty_color.text().strip() or "#F7DDE7",
                          accent_color=self.accent_color.text().strip() or "#9ED8EA",
                          logo_path=self._logo_path)

    def generate_series(self) -> None:
        model = CardModel.B if self.model.currentIndex() else CardModel.A
        generator = SeriesGenerator()
        generated = []
        try:
            for offset in range(self.quantity.value()):
                series = generator.generate(self.series_id.value() + offset, model=model,
                                            serial_start=self.serial_start.value() + offset * 6)
                self.repository.save(series)
                generated.append(series)
            self._series = generated[0]
            self.preview_label.setText(
                f"GENERADO Y GUARDADO\n{len(generated)} serie(s) · {len(generated) * 6} cartones\n"
                f"Series {generated[0].series_id}–{generated[-1].series_id}\n"
                f"Modelo {model.value}"
            )
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def _svg(self) -> str:
        if self._series is None: self.generate_series()
        if self._series is None: raise ValueError("No se pudo generar la serie")
        return A4SvgRenderer(style=self._style()).render(self._series.cards)

    def preview_a4(self) -> None:
        try:
            svg = self._svg()
            self.preview_label.setText(f"VISTA PREVIA A4 LISTA\nSerie {self._series.series_id}\n{len(svg):,} caracteres SVG")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error", str(exc))

    def save_a4(self) -> None:
        try:
            svg = self._svg()
            path, _ = QFileDialog.getSaveFileName(self, "Guardar hoja A4", "fb_bingo_serie.svg", "SVG (*.svg)")
            if path: Path(path).write_text(svg, encoding="utf-8")
        except (ValueError, OSError) as exc: QMessageBox.warning(self, "Error", str(exc))


GeneratorWindow = GeneratorWidget
