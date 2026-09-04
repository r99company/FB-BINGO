from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPixmap
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from app.cards import CardModel, SeriesGenerator
from app.printing import A4SvgRenderer, PrintStyle


class GeneratorWindow(QMainWindow):
    """Operator-facing generator: configure, generate and preview one series."""

    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("FB BINGO — Generador de Cartones")
        self.resize(1100, 760)
        self._series = None
        self._logo_path: str | None = None
        self._build_ui()

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)
        layout = QHBoxLayout(root)

        controls = QGroupBox("Configuración")
        form = QFormLayout(controls)
        self.model = QComboBox()
        self.model.addItems(["Modelo A", "Modelo B"])
        self.series_id = QLineEdit("1")
        self.serial_start = QSpinBox()
        self.serial_start.setRange(1, 30_000)
        self.serial_start.setValue(1)
        self.empty_color = QLineEdit("#F7DDE7")
        self.accent_color = QLineEdit("#9ED8EA")
        self.logo = QLabel("Sin logo")
        self.logo.setWordWrap(True)
        logo_button = QPushButton("Seleccionar logo")
        logo_button.clicked.connect(self._choose_logo)
        generate = QPushButton("GENERAR SERIE")
        generate.clicked.connect(self.generate_series)
        preview = QPushButton("VISTA PREVIA A4")
        preview.clicked.connect(self.preview_a4)
        save = QPushButton("GUARDAR A4 SVG")
        save.clicked.connect(self.save_a4)
        form.addRow("Modelo:", self.model)
        form.addRow("Serie:", self.series_id)
        form.addRow("Serial inicial:", self.serial_start)
        form.addRow("Color espacios vacíos:", self.empty_color)
        form.addRow("Color acento:", self.accent_color)
        form.addRow(self.logo, logo_button)
        form.addRow(generate)
        form.addRow(preview)
        form.addRow(save)
        layout.addWidget(controls, 0)

        self.preview_label = QLabel("Genera una serie para ver la información.")
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumWidth(700)
        self.preview_label.setStyleSheet("QLabel { border: 1px solid #9ED8EA; padding: 20px; }")
        layout.addWidget(self.preview_label, 1)

    def _choose_logo(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar logo", "", "Imágenes (*.png *.jpg *.jpeg)")
        if path:
            self._logo_path = path
            self.logo.setText(Path(path).name)

    def _style(self) -> PrintStyle:
        return PrintStyle(
            empty_cell_color=self.empty_color.text().strip() or "#F7DDE7",
            accent_color=self.accent_color.text().strip() or "#9ED8EA",
            logo_path=self._logo_path,
        )

    def generate_series(self) -> None:
        try:
            series_id = int(self.series_id.text().strip())
            if series_id < 1:
                raise ValueError
            model = CardModel.B if self.model.currentIndex() == 1 else CardModel.A
            self._series = SeriesGenerator().generate(
                series_id=series_id,
                model=model,
                serial_start=self.serial_start.value(),
            )
            self._show_series_summary()
        except ValueError:
            QMessageBox.warning(self, "Datos inválidos", "La serie debe ser un número entero positivo.")

    def _show_series_summary(self) -> None:
        assert self._series is not None
        cards = self._series.cards
        lines = [f"SERIE {self._series.series_id} — {len(cards)} cartones"]
        lines.extend(f"Cartón {i}: {card.serial} · Modelo {card.model.value}" for i, card in enumerate(cards, 1))
        self.preview_label.setText("\n".join(lines))

    def _svg(self) -> str:
        if self._series is None:
            self.generate_series()
        if self._series is None:
            raise ValueError("No se pudo generar la serie")
        return A4SvgRenderer(style=self._style()).render(self._series.cards)

    def preview_a4(self) -> None:
        try:
            svg = self._svg()
            self.preview_label.setText(
                f"Vista previa A4 lista\n\nSerie {self._series.series_id}\n"
                f"6 cartones · Modelo {self._series.cards[0].model.value}\n\n"
                f"{len(svg):,} caracteres SVG"
            )
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "No se pudo preparar la vista", str(exc))

    def save_a4(self) -> None:
        try:
            svg = self._svg()
            path, _ = QFileDialog.getSaveFileName(self, "Guardar hoja A4", "fb_bingo_serie.svg", "SVG (*.svg)")
            if path:
                Path(path).write_text(svg, encoding="utf-8")
                QMessageBox.information(self, "Listo", f"Hoja A4 guardada en:\n{path}")
        except (ValueError, OSError) as exc:
            QMessageBox.warning(self, "Error", str(exc))
