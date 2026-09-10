from __future__ import annotations

from collections.abc import Callable

from PySide6.QtCore import QEvent, QObject, Qt
from PySide6.QtGui import QAction, QKeyEvent
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QMessageBox, QPushButton, QWidget

from app.cards import CardModel


class _F4NewGameFilter(QObject):
    """Protege F4 para que nunca cambie de partida sin confirmación."""

    def eventFilter(self, watched: QObject, event: QEvent) -> bool:
        if event.type() != QEvent.Type.KeyPress:
            return super().eventFilter(watched, event)
        if not isinstance(event, QKeyEvent) or event.key() != Qt.Key.Key_F4:
            return super().eventFilter(watched, event)

        window = watched
        if not hasattr(window, "new_game"):
            return super().eventFilter(watched, event)

        answer = QMessageBox.question(
            window,
            "FB-BINGO · NUEVA PARTIDA",
            "¿Va a comenzar una nueva partida?\n\n"
            "Si selecciona SÍ, se cerrará la partida actual y se limpiarán las bolas llamadas.\n"
            "Si selecciona NO, la partida continuará exactamente como está.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )
        if answer == QMessageBox.StandardButton.Yes:
            window.new_game()
        return True


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


# La pantalla principal conserva los atajos F1-F4, pero los controles visuales
# dejan de ocupar espacio. La ayuda queda accesible desde el menú superior.
_original_bingo_main_window_init = None


def _install_clean_operator_ui() -> None:
    global _original_bingo_main_window_init
    try:
        from app.ui.main_window import BingoMainWindow
    except Exception:
        return
    if getattr(BingoMainWindow, "_fb_help_installed", False):
        return
    _original_bingo_main_window_init = BingoMainWindow.__init__

    def _init_with_clean_operator_ui(self, *args, **kwargs):
        _original_bingo_main_window_init(self, *args, **kwargs)
        # F4 queda protegido a nivel de ventana, antes de que QShortcut pueda
        # ejecutar su acción. Así un toque accidental nunca borra la partida.
        self._fb_f4_filter = _F4NewGameFilter(self)
        self.installEventFilter(self._fb_f4_filter)
        for button in self.findChildren(QPushButton):
            text = button.text()
            if "F1" in text or "F2" in text or "F3" in text or "F4" in text:
                button.hide()
        help_menu = self.menuBar().addMenu("❓ AYUDA")
        help_action = QAction("Controles F1-F4 y operación", self)
        help_action.triggered.connect(lambda: QMessageBox.information(
            self,
            "FB-BINGO · AYUDA Y CONTROLES",
            "<h2>🎱 Controles de la sala</h2>"
            "<p><b>F1</b> · 🎱 Jugar / sortear una nueva bola</p>"
            "<p><b>F2</b> · ⏸️ Pausar / reanudar la partida</p>"
            "<p><b>F3</b> · ↩️ Deshacer la última bola</p>"
            "<p><b>F4</b> · 🆕 Nueva partida (siempre pide confirmación)</p>"
            "<hr>"
            "<p><b>ENTER</b> · Registrar la bola física digitada.</p>"
            "<p>También puede pulsar directamente una bola del tablero para cantarla.</p>"
            "<p><b>F4</b> pregunta antes de cerrar la partida actual y comenzar una nueva.</p>",
        ))
        help_menu.addAction(help_action)
        self.menuBar().setStyleSheet(
            "QMenuBar { background:#050C22; color:#FFFFFF; font-weight:800; padding:4px 8px; } "
            "QMenuBar::item:selected { background:#D61A84; border-radius:5px; } "
            "QMenu { background:#07132D; color:#FFFFFF; border:1px solid #174A86; } "
            "QMenu::item:selected { background:#D61A84; }"
        )

    BingoMainWindow.__init__ = _init_with_clean_operator_ui
    BingoMainWindow._fb_help_installed = True


_install_clean_operator_ui()
