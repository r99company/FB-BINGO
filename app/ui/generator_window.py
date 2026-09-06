from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtSvgWidgets import QSvgWidget
from PySide6.QtWidgets import QComboBox, QFileDialog, QFormLayout, QGroupBox, QHBoxLayout, QLabel, QLineEdit, QMessageBox, QPushButton, QSpinBox, QVBoxLayout, QWidget

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.settings.paths import database_path


class GeneratorWidget(QWidget):
    """Generador profesional de series Modelo A y hoja A4 de seis cartones."""

    def __init__(self, repository: SQLiteSeriesRepository | None = None) -> None:
        super().__init__()
        self.repository = repository or SQLiteSeriesRepository(database_path())
        self._series = None
        self._logo_path: str | None = None
        self._svg = ""
        self._build_ui()

    def _build_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(18, 18, 18, 18)
        layout.setSpacing(16)

        controls = QGroupBox("GENERADOR DE CARTONES")
        controls.setMinimumWidth(330)
        form = QFormLayout(controls)

        # Modelo A es el único modelo de producción de esta versión.
        # El núcleo conserva CardModel.B para una futura incorporación segura.
        self.model = QComboBox()
        self.model.addItem("Modelo A", CardModel.A.value)

        self.series_id = QSpinBox(); self.series_id.setRange(1, 999999); self.series_id.setValue(1)
        self.quantity = QSpinBox(); self.quantity.setRange(1, 2500); self.quantity.setValue(1)
        self.serial_start = QSpinBox(); self.serial_start.setRange(1, 29995); self.serial_start.setValue(1)
        self.empty_color = QLineEdit("#F2E9FF")
        self.accent_color = QLineEdit("#FF4FA3")
        self.secondary_color = QLineEdit("#8FD9FF")
        self.logo = QLabel("Sin logo seleccionado"); self.logo.setObjectName("Muted"); self.logo.setWordWrap(True)

        # La decisión de QR es exclusivamente de impresión: no cambia el
        # cartón, sus números, su serial ni la lógica de verificación.
        self.qr = QComboBox()
        self.qr.addItem("SIN QR — sin zona reservada", False)
        self.qr.addItem("CON QR — reservar zona", True)

        logo_button = QPushButton("SELECCIONAR LOGO"); logo_button.setObjectName("Secondary"); logo_button.clicked.connect(self._choose_logo)
        generate = QPushButton("GENERAR SERIES"); generate.setObjectName("Primary"); generate.clicked.connect(self.generate_series)
        preview = QPushButton("ACTUALIZAR VISTA A4"); preview.setObjectName("Secondary"); preview.clicked.connect(self.preview_a4)
        save = QPushButton("GUARDAR A4 (SVG)"); save.setObjectName("Secondary"); save.clicked.connect(self.save_a4)

        for label, widget in (("Modelo", self.model), ("Serie inicial", self.series_id), ("Cantidad de series", self.quantity), ("Serial inicial", self.serial_start), ("Color espacios", self.empty_color), ("Color principal", self.accent_color), ("Color secundario", self.secondary_color), ("QR", self.qr)):
            form.addRow(label, widget)
        form.addRow(self.logo, logo_button)
        form.addRow(generate)
        form.addRow(preview)
        form.addRow(save)

        info = QLabel(
            "Producción actual: Modelo A. Cada serie contiene 6 cartones y cubre "
            "las 90 bolas exactamente una vez. El QR es opcional y solo afecta "
            "el diseño de impresión."
        )
        info.setObjectName("Muted"); info.setWordWrap(True)
        form.addRow(info)
        layout.addWidget(controls)

        preview_panel = QGroupBox("VISTA PREVIA — A4 / 6 CARTONES")
        preview_layout = QVBoxLayout(preview_panel)
        self.preview_widget = QSvgWidget()
        self.preview_widget.setMinimumSize(650, 760)
        self.preview_widget.setStyleSheet("background:#FFFFFF;border:1px solid #34405B;border-radius:12px;")
        preview_layout.addWidget(self.preview_widget, 1)
        self.preview_label = QLabel("Genera una serie para visualizar la hoja A4.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setObjectName("Muted")
        preview_layout.addWidget(self.preview_label)
        layout.addWidget(preview_panel, 1)

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo FB-BINGO", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path
            self.logo.setText(Path(path).name)
            self.preview_a4()

    def _style(self) -> PrintStyle:
        return PrintStyle(
            empty_cell_color=self.empty_color.text().strip() or "#F2E9FF",
            accent_color=self.accent_color.text().strip() or "#FF4FA3",
            secondary_accent_color=self.secondary_color.text().strip() or "#8FD9FF",
            logo_path=self._logo_path,
            show_model=False,
            show_serial=True,
            show_qr_zone=bool(self.qr.currentData()),
        )

    def generate_series(self) -> None:
        # El selector está limitado deliberadamente a Modelo A durante la fase
        # de producción inicial, aunque el núcleo sigue siendo model-aware.
        model = CardModel(self.model.currentData())
        generator = SeriesGenerator()
        generated = []
        try:
            for offset in range(self.quantity.value()):
                series = generator.generate(
                    self.series_id.value() + offset,
                    model=model,
                    serial_start=self.serial_start.value() + offset * 6,
                )
                self.repository.save(series)
                generated.append(series)
            self._series = generated[0]
            self._render_preview()
            qr_text = "CON QR" if self.qr.currentData() else "SIN QR"
            self.preview_label.setText(f"GENERADO · {len(generated)} serie(s) · {len(generated) * 6} cartones · Serie {generated[0].series_id}–{generated[-1].series_id} · {qr_text}")
        except (ValueError, RuntimeError) as exc:
            QMessageBox.warning(self, "No se pudo generar", str(exc))

    def _render_preview(self) -> None:
        if self._series is None:
            raise ValueError("No se pudo generar la serie")
        self._svg = A4SvgRenderer(style=self._style()).render(self._series.cards)
        self.preview_widget.load(self._svg.encode("utf-8"))

    def preview_a4(self) -> None:
        try:
            if self._series is None:
                self.generate_series()
                return
            self._render_preview()
            qr_text = "CON QR" if self.qr.currentData() else "SIN QR"
            self.preview_label.setText(f"Vista A4 · Serie {self._series.series_id} · 6 cartones · {qr_text}")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error de vista previa", str(exc))

    def save_a4(self) -> None:
        try:
            if self._series is None:
                self.generate_series()
            if self._series is None:
                raise ValueError("No hay una serie generada")
            svg = self._svg or A4SvgRenderer(style=self._style()).render(self._series.cards)
            path, _ = QFileDialog.getSaveFileName(self, "Guardar hoja A4", f"fb_bingo_serie_{self._series.series_id}.svg", "SVG (*.svg)")
            if path:
                Path(path).write_text(svg, encoding="utf-8")
                QMessageBox.information(self, "A4 guardado", "La hoja A4 fue guardada correctamente.")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error al guardar", str(exc))


GeneratorWindow = GeneratorWidget
