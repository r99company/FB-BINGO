from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QWidget

from app.cards import CardModel


class GameModelSelector(QWidget):
    """Selector del modelo de cartón usado por la partida actual.

    Modelo A es el predeterminado. El operador puede cambiar A/B entre
    partidas, pero no mientras ya haya bolas jugadas, evitando mezclar
    modelos dentro de una misma partida.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.current_model = CardModel.A
        self._changing = False
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

    def _on_changed(self, index: int) -> None:
        if self._changing:
            return
        self.current_model = self.combo.itemData(index)

    def set_model(self, model: CardModel) -> None:
        self._changing = True
        try:
            index = self.combo.findData(model)
            if index >= 0:
                self.combo.setCurrentIndex(index)
            self.current_model = model
        finally:
            self._changing = False

    def guard_change(self, has_balls: bool) -> bool:
        """Permite A/B libremente entre partidas, no a mitad de una partida."""
        selected = self.combo.currentData()
        if not has_balls:
            self.current_model = selected
            return True
        if selected == self.current_model:
            return True
        self._changing = True
        try:
            self.combo.setCurrentIndex(self.combo.findData(self.current_model))
        finally:
            self._changing = False
        QMessageBox.warning(
            self,
            "FB-BINGO · MODELO DE CARTÓN",
            "No se puede cambiar el modelo con la partida en curso.\n\n"
            "Finalice la partida y seleccione Modelo A o Modelo B para la siguiente partida.",
        )
        return False
