from __future__ import annotations

from collections.abc import Callable

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QWidget

from app.cards import CardModel


class GameModelSelector(QWidget):
    """Selector del modelo de cartón usado por la partida actual."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_model = CardModel.A
        self._changing = False
        self._can_change: Callable[[], bool] | None = None
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)
        label = QLabel("MODELO")
        label.setStyleSheet("font-weight:900;color:#AFC7E8;")
        self.combo = QComboBox()
        self.combo.addItem("A · PRINCIPAL", CardModel.A)
        self.combo.addItem("B · ESPECIAL", CardModel.B)
        self.combo.setCurrentIndex(0)
        self.combo.setToolTip("Seleccione el modelo de cartón para la próxima partida")
        self.combo.currentIndexChanged.connect(self._on_changed)
        layout.addWidget(label)
        layout.addWidget(self.combo)

    def set_change_guard(self, callback: Callable[[], bool]) -> None:
        self._can_change = callback

    def _on_changed(self, index: int) -> None:
        if self._changing:
            return
        selected = self.combo.itemData(index)
        if self._can_change is not None and not self._can_change():
            self._changing = True
            try:
                self.combo.setCurrentIndex(self.combo.findData(self.current_model))
            finally:
                self._changing = False
            QMessageBox.warning(
                self,
                "FB-BINGO · MODELO DE CARTÓN",
                "La partida ya tiene bolas jugadas.\n\n"
                "Finalice esta partida para poder cambiar de Modelo A a Modelo B o viceversa.",
            )
            return
        self.current_model = selected

    def set_model(self, model: CardModel) -> None:
        self._changing = True
        try:
            index = self.combo.findData(model)
            if index >= 0:
                self.combo.setCurrentIndex(index)
            self.current_model = model
        finally:
            self._changing = False
