from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, Qt, QThread, Signal
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
    QProgressBar,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.cards import BulkGenerationResult, BulkSeriesGenerator, CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle


class BulkGenerationWorker(QObject):
    """Ejecuta la generación masiva fuera del hilo de la interfaz."""

    progress = Signal(int, int, int)
    finished = Signal(object)
    error = Signal(str)

    def __init__(self, repository, *, start_series, quantity, model, serial_start, seed=None):
        super().__init__()
        self.repository = repository
        self.start_series = start_series
        self.quantity = quantity
        self.model = model
        self.serial_start = serial_start
        self.seed = seed

    def run(self) -> None:
        try:
            generator = BulkSeriesGenerator(self.repository, seed=self.seed)
            result = generator.generate(
                start_series=self.start_series,
                quantity=self.quantity,
                model=self.model,
                serial_start=self.serial_start,
                progress=self._report_progress,
            )
            self.finished.emit(result)
        except Exception as exc:  # noqa: BLE001 - se informa a la interfaz
            self.error.emit(str(exc))

    def _report_progress(self, current: int, total: int) -> None:
        self.progress.emit(current, total, current * 6)


class GeneratorWidget(QWidget):
    """Generator UI embeddable as a tab in the main application."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(Path("data") / "fb_bingo.db")
        self._series = None
        self._logo_path: str | None = None
        self._bulk_thread: QThread | None = None
        self._bulk_worker: BulkGenerationWorker | None = None
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
        self.bulk_generate = QPushButton("GENERACIÓN MASIVA — 2.500 SERIES")
        self.bulk_generate.clicked.connect(self.generate_bulk)
        self.preview = QPushButton("VISTA PREVIA A4"); self.preview.clicked.connect(self.preview_a4)
        self.save = QPushButton("GUARDAR A4 SVG"); self.save.clicked.connect(self.save_a4)

        self.bulk_progress = QProgressBar(); self.bulk_progress.setRange(0, 2_500); self.bulk_progress.setValue(0)
        self.bulk_progress.setFormat("Serie %v / %m")
        self.bulk_status = QLabel("Listo para generar 2.500 series (15.000 cartones).")
        self.bulk_status.setWordWrap(True)

        for label, widget in (("Modelo:", self.model), ("Serie inicial:", self.series_id),
                              ("Cantidad de series:", self.quantity), ("Serial inicial:", self.serial_start),
                              ("Color espacios vacíos:", self.empty_color), ("Color acento:", self.accent_color)):
            form.addRow(label, widget)
        form.addRow(self.logo, logo_button)
        form.addRow(generate); form.addRow(self.bulk_generate); form.addRow(self.bulk_progress)
        form.addRow(self.bulk_status); form.addRow(self.preview); form.addRow(self.save)
        layout.addWidget(controls)

        self.preview_label = QLabel("Configura y genera una serie.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setStyleSheet("border: 1px solid #9ED8EA; padding: 20px;")
        layout.addWidget(self.preview_label, 1)

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg *.webp)"
        )
        if path:
            self._logo_path = path; self.logo.setText(Path(path).name)

    def _style(self) -> PrintStyle:
        return PrintStyle(empty_cell_color=self.empty_color.text().strip() or "#F7DDE7",
                          accent_color=self.accent_color.text().strip() or "#9ED8EA",
                          logo_path=self._logo_path)

    def _selected_model(self) -> CardModel:
        return CardModel.B if self.model.currentIndex() else CardModel.A

    def generate_series(self) -> None:
        model = self._selected_model(); generator = SeriesGenerator(); generated = []
        try:
            for offset in range(self.quantity.value()):
                series = generator.generate(self.series_id.value() + offset, model=model,
                                            serial_start=self.serial_start.value() + offset * 6)
                self.repository.save(series); generated.append(series)
            self._series = generated[0]
            self.preview_label.setText(
                f"GENERADO Y GUARDADO\n{len(generated)} serie(s) · {len(generated) * 6} cartones\n"
                f"Series {generated[0].series_id}–{generated[-1].series_id}\nModelo {model.value}"
            )
        except ValueError as exc:
            QMessageBox.warning(self, "No se pudo guardar", str(exc))

    def generate_bulk(self) -> None:
        if self._bulk_thread is not None and self._bulk_thread.isRunning():
            return
        model = self._selected_model(); quantity = self.quantity.value()
        self.bulk_progress.setRange(0, quantity); self.bulk_progress.setValue(0)
        self.bulk_status.setText(f"Generando {quantity:,} series · {quantity * 6:,} cartones...")
        for widget in (self.bulk_generate, self.preview, self.save, self.model,
                       self.series_id, self.quantity, self.serial_start):
            widget.setEnabled(False)

        self._bulk_thread = QThread(self)
        self._bulk_worker = BulkGenerationWorker(
            self.repository, start_series=self.series_id.value(), quantity=quantity,
            model=model, serial_start=self.serial_start.value()
        )
        self._bulk_worker.moveToThread(self._bulk_thread)
        self._bulk_thread.started.connect(self._bulk_worker.run)
        self._bulk_worker.progress.connect(self._on_bulk_progress)
        self._bulk_worker.finished.connect(self._on_bulk_finished)
        self._bulk_worker.error.connect(self._on_bulk_error)
        self._bulk_worker.finished.connect(self._bulk_thread.quit)
        self._bulk_worker.error.connect(self._bulk_thread.quit)
        self._bulk_thread.finished.connect(self._bulk_cleanup)
        self._bulk_thread.start()

    def _on_bulk_progress(self, current: int, total: int, cards: int) -> None:
        self.bulk_progress.setRange(0, total); self.bulk_progress.setValue(current)
        self.bulk_status.setText(f"Serie {current:,} / {total:,} · Cartones {cards:,} / {total * 6:,}")

    def _on_bulk_finished(self, result: BulkGenerationResult) -> None:
        self._series = self.repository.get(str(result.first_series))
        self.bulk_progress.setValue(result.series_generated)
        self.bulk_status.setText(
            f"COMPLETADO · {result.series_generated:,} series · {result.cards_generated:,} cartones\n"
            f"Series {result.first_series}–{result.last_series} · Seriales {result.first_serial:,}–{result.last_serial:,}"
        )
        self.preview_label.setText(
            "GENERACIÓN MASIVA COMPLETADA\n"
            f"{result.series_generated:,} series · {result.cards_generated:,} cartones\n"
            f"Modelo {self._series.cards[0].model.value}\nSerie actual: {self._series.series_id}"
        )

    def _on_bulk_error(self, message: str) -> None:
        self.bulk_status.setText(f"ERROR: {message}")
        QMessageBox.critical(self, "Generación masiva", message)

    def _bulk_cleanup(self) -> None:
        for widget in (self.bulk_generate, self.preview, self.save, self.model,
                       self.series_id, self.quantity, self.serial_start):
            widget.setEnabled(True)
        if self._bulk_thread is not None:
            self._bulk_thread.deleteLater()
        self._bulk_thread = None; self._bulk_worker = None

    def _svg(self) -> str:
        if self._series is None: self.generate_series()
        if self._series is None: raise ValueError("No se pudo generar la serie")
        return A4SvgRenderer(style=self._style()).render(self._series.cards)

    def preview_a4(self) -> None:
        try:
            svg = self._svg()
            self.preview_label.setText(f"VISTA PREVIA A4 LISTA\nSerie {self._series.series_id}\n{len(svg):,} caracteres SVG")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error", str(exc))

    def save_a4(self) -> None:
        try:
            svg = self._svg()
            path, _ = QFileDialog.getSaveFileName(self, "Guardar hoja A4", "fb_bingo_serie.svg", "SVG (*.svg)")
            if path: Path(path).write_text(svg, encoding="utf-8")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error", str(exc))


GeneratorWindow = GeneratorWidget
