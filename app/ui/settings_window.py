from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import (
    QFileDialog, QComboBox, QFormLayout, QHBoxLayout, QLabel, QLineEdit,
    QMainWindow, QMessageBox, QPushButton, QCheckBox, QDoubleSpinBox,
    QSpinBox, QVBoxLayout, QWidget,
)

from app.settings.service import SettingsService


class SettingsWindow(QMainWindow):
    """Configuración operativa, premios, TV y conexión entre PCs de FB-BINGO."""

    def __init__(self, settings_path: str | Path) -> None:
        super().__init__()
        self.setWindowTitle("FB-BINGO — Configuración")
        self.resize(760, 760)
        self.service = SettingsService(settings_path)
        root = QWidget()
        self.setCentralWidget(root)
        layout = QVBoxLayout(root)
        title = QLabel("⚙ CONFIGURACIÓN DEL SISTEMA")
        title.setStyleSheet("font-size:20px;font-weight:900;")
        layout.addWidget(title)

        form = QFormLayout()
        self.business_name = QLineEdit(str(self.service.get("business_name", "FB-BINGO")))
        self.operator_name = QLineEdit(str(self.service.get("operator_name", "")))
        form.addRow("Nombre del negocio:", self.business_name)
        form.addRow("Operador:", self.operator_name)
        layout.addLayout(form)

        station_title = QLabel("RED · DOS COMPUTADORAS")
        station_title.setStyleSheet("font-size:16px;font-weight:900;margin-top:10px;")
        layout.addWidget(station_title)
        station_form = QFormLayout()
        self.station_role = QComboBox()
        self.station_role.addItem("LOCUTORA · EQUIPO QUE DIGITA LAS BOLAS", "locutora")
        self.station_role.addItem("ADMINISTRADOR · RECIBE LAS BOLAS AUTOMÁTICAMENTE", "administrador")
        current_role = str(self.service.get("station_role", "locutora")).lower()
        index = self.station_role.findData(current_role)
        self.station_role.setCurrentIndex(index if index >= 0 else 0)
        station_form.addRow("Función de esta PC:", self.station_role)
        layout.addLayout(station_form)
        station_hint = QLabel(
            "La PC LOCUTORA es la autoridad de la partida: cuando digita 26, la PC ADMINISTRADOR "
            "recibe y marca el 26 automáticamente. Ambas deben estar en la misma red local."
        )
        station_hint.setWordWrap(True)
        station_hint.setStyleSheet("color:#555;font-size:11px;")
        layout.addWidget(station_hint)

        prize_title = QLabel("PREMIOS")
        prize_title.setStyleSheet("font-size:16px;font-weight:900;margin-top:10px;")
        layout.addWidget(prize_title)
        prize_form = QFormLayout()
        self.line_prize = self._percent_spin("line_prize_percent")
        self.bingo_prize = self._percent_spin("bingo_prize_percent")
        self.series_line_prize = self._percent_spin("series_line_prize_percent")
        self.series_bingo_prize = self._percent_spin("series_bingo_prize_percent")
        prize_form.addRow("Partida rápida · Línea (%):", self.line_prize)
        prize_form.addRow("Partida rápida · Bingo (%):", self.bingo_prize)
        prize_form.addRow("Serie · Línea (%):", self.series_line_prize)
        prize_form.addRow("Serie · Bingo (%):", self.series_bingo_prize)
        layout.addLayout(prize_form)

        tv_title = QLabel("CONEXIÓN · IP Y PUERTO")
        tv_title.setStyleSheet("font-size:16px;font-weight:900;margin-top:10px;")
        layout.addWidget(tv_title)
        tv_form = QFormLayout()
        self.tv_host = QLineEdit(str(self.service.get("tv_server_host", "127.0.0.1")))
        self.tv_port = QSpinBox()
        self.tv_port.setRange(1, 65535)
        self.tv_port.setValue(int(self.service.get("tv_server_port", 8765)))
        self.tv_host.setPlaceholderText("IP de la PC locutora, por ejemplo 192.168.1.10")
        tv_form.addRow("IP / nombre de la PC locutora:", self.tv_host)
        tv_form.addRow("Puerto de sincronización:", self.tv_port)
        layout.addLayout(tv_form)
        tv_hint = QLabel(
            "En la PC LOCUTORA puede dejar la IP en blanco/127.0.0.1. En la PC ADMINISTRADOR "
            "coloque la IP de la PC LOCUTORA. El puerto debe ser igual en ambas."
        )
        tv_hint.setWordWrap(True)
        tv_hint.setStyleSheet("color:#555;font-size:11px;")
        layout.addWidget(tv_hint)

        self.hide_sales = QCheckBox("Ocultar cantidades de ventas en la pantalla principal")
        self.hide_sales.setChecked(bool(self.service.get("hide_sales_counts", False)))
        self.hide_production = QCheckBox("Ocultar cantidades de producción")
        self.hide_production.setChecked(bool(self.service.get("hide_production_counts", False)))
        self.tv_internal = QCheckBox("Mostrar información interna en pantalla TV")
        self.tv_internal.setChecked(bool(self.service.get("tv_show_internal_counts", False)))
        layout.addWidget(self.hide_sales)
        layout.addWidget(self.hide_production)
        layout.addWidget(self.tv_internal)

        buttons = QHBoxLayout()
        save = QPushButton("GUARDAR")
        save.clicked.connect(self.save)
        backup = QPushButton("RESPALDAR CONFIGURACIÓN")
        backup.clicked.connect(self.backup)
        restore = QPushButton("RESTAURAR CONFIGURACIÓN")
        restore.clicked.connect(self.restore)
        buttons.addWidget(save)
        buttons.addWidget(backup)
        buttons.addWidget(restore)
        layout.addLayout(buttons)
        layout.addStretch()

    def _percent_spin(self, key: str) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 100.0)
        spin.setDecimals(2)
        spin.setSingleStep(5.0)
        spin.setSuffix(" %")
        spin.setValue(float(self.service.get(key, 0.0)))
        return spin

    def save(self) -> None:
        values = (
            self.line_prize.value(), self.bingo_prize.value(),
            self.series_line_prize.value(), self.series_bingo_prize.value(),
        )
        if any(value < 0 or value > 100 for value in values):
            QMessageBox.warning(self, "FB-BINGO", "Los premios deben estar entre 0 % y 100 %.")
            return
        role = self.station_role.currentData() or "locutora"
        host = self.tv_host.text().strip()
        if role == "administrador" and not host:
            QMessageBox.warning(self, "FB-BINGO", "En la PC ADMINISTRADOR debe indicar la IP de la PC LOCUTORA.")
            return
        self.service.set("business_name", self.business_name.text().strip() or "FB-BINGO")
        self.service.set("operator_name", self.operator_name.text().strip())
        self.service.set("station_role", role)
        self.service.set("hide_sales_counts", self.hide_sales.isChecked())
        self.service.set("hide_production_counts", self.hide_production.isChecked())
        self.service.set("tv_show_internal_counts", self.tv_internal.isChecked())
        self.service.set("line_prize_percent", self.line_prize.value())
        self.service.set("bingo_prize_percent", self.bingo_prize.value())
        self.service.set("series_line_prize_percent", self.series_line_prize.value())
        self.service.set("series_bingo_prize_percent", self.series_bingo_prize.value())
        self.service.set("tv_server_host", host or "127.0.0.1")
        self.service.set("tv_server_port", self.tv_port.value())
        self.service.save()
        QMessageBox.information(
            self,
            "FB-BINGO",
            "Configuración guardada. Reinicie FB-BINGO en ambas computadoras para aplicar el rol de red.",
        )

    def backup(self) -> None:
        target, _ = QFileDialog.getSaveFileName(self, "Guardar respaldo", "fb-bingo-settings.json", "JSON (*.json)")
        if target:
            self.service.save()
            self.service.backup(target)
            QMessageBox.information(self, "FB-BINGO", "Respaldo creado correctamente.")

    def restore(self) -> None:
        source, _ = QFileDialog.getOpenFileName(self, "Seleccionar respaldo", "", "JSON (*.json)")
        if source:
            try:
                self.service.restore(source)
                self.service.load()
                self._load_fields()
                QMessageBox.information(self, "FB-BINGO", "Configuración restaurada correctamente.")
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "FB-BINGO", f"No se pudo restaurar el respaldo: {exc}")

    def _load_fields(self) -> None:
        self.business_name.setText(str(self.service.get("business_name", "FB-BINGO")))
        self.operator_name.setText(str(self.service.get("operator_name", "")))
        self.station_role.setCurrentIndex(max(0, self.station_role.findData(str(self.service.get("station_role", "locutora")))))
        self.hide_sales.setChecked(bool(self.service.get("hide_sales_counts", False)))
        self.hide_production.setChecked(bool(self.service.get("hide_production_counts", False)))
        self.tv_internal.setChecked(bool(self.service.get("tv_show_internal_counts", False)))
        self.line_prize.setValue(float(self.service.get("line_prize_percent", 40.0)))
        self.bingo_prize.setValue(float(self.service.get("bingo_prize_percent", 60.0)))
        self.series_line_prize.setValue(float(self.service.get("series_line_prize_percent", 50.0)))
        self.series_bingo_prize.setValue(float(self.service.get("series_bingo_prize_percent", 50.0)))
        self.tv_host.setText(str(self.service.get("tv_server_host", "127.0.0.1")))
        self.tv_port.setValue(int(self.service.get("tv_server_port", 8765)))
