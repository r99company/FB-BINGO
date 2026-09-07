from __future__ import annotations

from pathlib import Path

from PySide6.QtWidgets import QFileDialog, QFormLayout, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QCheckBox, QVBoxLayout, QWidget

from app.settings.service import SettingsService


class SettingsWindow(QMainWindow):
    """Configuración operativa y respaldo de preferencias de FB-BINGO."""

    def __init__(self, settings_path: str | Path) -> None:
        super().__init__()
        self.setWindowTitle("FB-BINGO — Configuración")
        self.resize(620, 480)
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

    def save(self) -> None:
        self.service.set("business_name", self.business_name.text().strip() or "FB-BINGO")
        self.service.set("operator_name", self.operator_name.text().strip())
        self.service.set("hide_sales_counts", self.hide_sales.isChecked())
        self.service.set("hide_production_counts", self.hide_production.isChecked())
        self.service.set("tv_show_internal_counts", self.tv_internal.isChecked())
        self.service.save()
        QMessageBox.information(self, "FB-BINGO", "Configuración guardada correctamente.")

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
                self.business_name.setText(str(self.service.get("business_name", "FB-BINGO")))
                self.operator_name.setText(str(self.service.get("operator_name", "")))
                self.hide_sales.setChecked(bool(self.service.get("hide_sales_counts", False)))
                self.hide_production.setChecked(bool(self.service.get("hide_production_counts", False)))
                self.tv_internal.setChecked(bool(self.service.get("tv_show_internal_counts", False)))
                QMessageBox.information(self, "FB-BINGO", "Configuración restaurada correctamente.")
            except (OSError, ValueError) as exc:
                QMessageBox.critical(self, "FB-BINGO", f"No se pudo restaurar el respaldo: {exc}")
