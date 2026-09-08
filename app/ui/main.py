from __future__ import annotations

import sys
import threading

from PySide6.QtCore import QTimer, Qt
from PySide6.QtGui import QKeySequence, QShortcut
from PySide6.QtWidgets import QApplication, QPushButton

from app.database import SQLiteGameHistoryRepository, SQLiteSeriesRepository
from app.sales import SalesService
from app.services import GameClosureService, GameHistoryService
from app.settings.paths import application_data_dir, database_path
from app.settings.service import SettingsService
from app.tv_sync import GameSyncClient, GameSyncServer, wire_operational_controls
from app.ui.cartons_window import CartonsWindow
from app.ui.main_window import BingoMainWindow, TVWindow
from app.ui.model_selector import GameModelSelector
from app.ui.reports_window import ReportsWindow
from app.ui.sales_window import SalesWindow
from app.ui.settings_window import SettingsWindow
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService

_original_init = BingoMainWindow.__init__
_original_enter_ball = BingoMainWindow.enter_ball
_original_draw_number = BingoMainWindow.draw_number
_original_call_number = BingoMainWindow.call_number
_original_undo_number = BingoMainWindow.undo_number
_original_toggle_pause = BingoMainWindow.toggle_pause
_original_new_game = BingoMainWindow.new_game
_original_open_tv = BingoMainWindow.open_tv


def _open_cartons(self: BingoMainWindow) -> None:
    if getattr(self, "cartons_window", None) is None:
        self.cartons_window = CartonsWindow()
        self.cartons_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
        self.generator_window = self.cartons_window
    self.show_cartons_window()


def _show_window(window) -> None:
    window.show()
    window.raise_()
    window.activateWindow()


def _show_cartons(self: BingoMainWindow) -> None:
    _show_window(self.cartons_window)

BingoMainWindow.show_cartons_window = lambda self: _show_cartons(self)


def _open_sales(self: BingoMainWindow) -> None:
    if getattr(self, "sales_window", None) is None:
        self.sales_window = SalesWindow(database_path())
        self.sales_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    _show_window(self.sales_window)


def _open_verification(self: BingoMainWindow) -> None:
    repository = SQLiteSeriesRepository(database_path())
    sales = SalesService(database_path(), repository=repository)
    service = VerificationService(repository, sales)
    if getattr(self, "verification_window", None) is None:
        self.verification_window = VerificationWindow(
            called_numbers=self.game.history,
            verification_service=service,
            expected_model=self.model_selector.current_model,
        )
        self.verification_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    else:
        self.verification_window.called_numbers = self.game.history
        self.verification_window.set_expected_model(self.model_selector.current_model)
    _show_window(self.verification_window)
    self.verification_window.serial_input.setFocus()


def _open_reports(self: BingoMainWindow) -> None:
    if getattr(self, "reports_window", None) is None:
        self.reports_window = ReportsWindow(self.history_repository, database_path().parent / "reports")
        self.reports_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    self.reports_window.refresh()
    _show_window(self.reports_window)


def _open_settings(self: BingoMainWindow) -> None:
    if getattr(self, "settings_window", None) is None:
        self.settings_window = SettingsWindow(application_data_dir() / "settings.json")
        self.settings_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    _show_window(self.settings_window)


def _publish_tv(self: BingoMainWindow) -> None:
    client = getattr(self, "tv_sync_client", None)
    if client is None:
        return
    try:
        client.publish({
            "current": self.game.current_number,
            "history": list(self.game.history),
            "game": self.header_values[0].text() or "PARTIDA RÁPIDA",
            "series": self.header_values[2].text() or "—",
            "model": self.model_selector.current_model.value,
            "status": "FINALIZADA" if getattr(self, "_finalized", False) else ("PAUSADA" if self.game.state.paused else "EN CURSO"),
        })
    except (OSError, ValueError, TimeoutError):
        pass


def _open_tv(self: BingoMainWindow) -> None:
    if getattr(self, "tv_window", None) is None:
        self.tv_window = TVWindow(self)
        self.tv_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    _show_window(self.tv_window)
    self.tv_window.update_game(self.game.current_number, self.game.last_five)
    _publish_tv(self)


def _history_sync(self) -> None:
    game_id = getattr(self, "history_game_id", None)
    if game_id is not None:
        self.history_service.sync(game_id, self.game)


def _start_history_game(self) -> None:
    self.history_game_id = self.history_service.start(self.game, game_name=self.header_values[0].text() or "PARTIDA RÁPIDA", series_id=self.header_values[2].text() or "—")


def _enter_ball_with_history(self) -> bool:
    if getattr(self, "_finalized", False):
        self.ball_message.setText("✕ PARTIDA FINALIZADA · INICIE UNA NUEVA PARTIDA")
        self.ball_input.selectAll()
        self.ball_input.setFocus()
        return False
    if self.game.state.paused:
        self.ball_message.setText("Ⅱ PARTIDA PAUSADA · NO SE PUEDE DIGITAR")
        self.ball_input.selectAll()
        self.ball_input.setFocus()
        return False
    result = _original_enter_ball(self)
    if result:
        _history_sync(self)
        _publish_tv(self)
    return result


def _draw_with_history(self) -> None:
    if getattr(self, "_finalized", False):
        self.ball_message.setText("✕ PARTIDA FINALIZADA · INICIE UNA NUEVA PARTIDA")
        return
    _original_draw_number(self)
    _history_sync(self)
    _publish_tv(self)


def _call_with_history(self, number: int) -> None:
    if getattr(self, "_finalized", False):
        self.ball_message.setText("✕ PARTIDA FINALIZADA · INICIE UNA NUEVA PARTIDA")
        return
    if self.game.state.paused:
        self.ball_message.setText("Ⅱ PARTIDA PAUSADA · NO SE PUEDE CANTAR BOLA")
        return
    _original_call_number(self, number)
    _history_sync(self)
    _publish_tv(self)


def _undo_with_history(self) -> None:
    if getattr(self, "_finalized", False):
        self.ball_message.setText("✕ PARTIDA FINALIZADA · NO SE PUEDE DESHACER")
        return
    was_paused = self.game.state.paused
    _original_undo_number(self)
    if was_paused and self.game.history:
        self.game.pause()
        self._sync_ui()
    _history_sync(self)
    _publish_tv(self)


def _pause_with_history(self) -> None:
    if getattr(self, "_finalized", False):
        self.ball_message.setText("✕ PARTIDA FINALIZADA · INICIE UNA NUEVA PARTIDA")
        return
    _original_toggle_pause(self)
    _history_sync(self)
    _publish_tv(self)


def _finalize_game_with_history(self) -> None:
    if getattr(self, "_finalized", False):
        return
    old_game_id = getattr(self, "history_game_id", None)
    export_error: Exception | None = None
    if old_game_id is not None:
        try:
            GameClosureService(self.history_repository, database_path().parent / "reports").close(
                old_game_id,
                self.game,
                game_name=self.header_values[0].text() or "PARTIDA RÁPIDA",
                series_id=self.header_values[2].text() or "—",
            )
        except Exception as exc:
            export_error = exc
    self._finalized = True
    self.game.resume()
    self.header_values[1].setText("FINALIZADA")
    self.ball_message.setText(
        "✓ PARTIDA FINALIZADA · EXCEL GENERADO" if export_error is None else "✓ PARTIDA FINALIZADA · EXCEL NO GENERADO"
    )
    self.ball_input.clear()
    self.ball_input.setEnabled(False)
    self._sync_ui()
    self.header_values[1].setText("FINALIZADA")
    _publish_tv(self)
    for button in self.findChildren(QPushButton):
        if button.text().startswith("■ FINALIZAR") or button.property("fb_bingo_finish_button") is True:
            button.setProperty("fb_bingo_finish_button", True)
            button.setText("▶ NUEVA PARTIDA\nF4")
            button.style().unpolish(button)
            button.style().polish(button)


def _new_game_with_history(self) -> None:
    if not getattr(self, "_finalized", False):
        _finalize_game_with_history(self)
    _original_new_game(self)
    self._finalized = False
    self.ball_input.setEnabled(True)
    self.ball_message.setText("NUEVA PARTIDA · ESPERANDO BOLA FÍSICA")
    self._sync_ui()
    self.header_values[1].setText("EN ESPERA")
    _start_history_game(self)
    for button in self.findChildren(QPushButton):
        if button.property("fb_bingo_finish_button") is True:
            button.setText("■ FINALIZAR\nF4")
            button.setProperty("fb_bingo_finish_button", True)
            button.style().unpolish(button)
            button.style().polish(button)
    _publish_tv(self)


def _replace_signal_connection(signal, slot) -> None:
    try:
        signal.disconnect()
    except (RuntimeError, TypeError):
        pass
    signal.connect(slot)


def _install_operator_shortcuts(self: BingoMainWindow) -> None:
    """Atajos reales de teclado para la operación de la partida."""
    self._operator_shortcuts = []
    actions = (
        ("F1", self.draw_number),
        ("F2", self.toggle_pause),
        ("F3", self.undo_number),
        ("F4", lambda: self.new_game() if getattr(self, "_finalized", False) else self.finalize_game()),
    )
    for sequence, callback in actions:
        shortcut = QShortcut(QKeySequence(sequence), self)
        shortcut.setContext(Qt.ShortcutContext.WindowShortcut)
        shortcut.activated.connect(callback)
        self._operator_shortcuts.append(shortcut)


def _install_model_selector(self: BingoMainWindow) -> None:
    """Instala el selector A/B en la cabecera de operación."""
    self.model_selector = GameModelSelector(self)
    self.model_selector.set_change_guard(
        lambda: not self.game.history or getattr(self, "_finalized", False)
    )
    top = self.series_label.parentWidget()
    row = top.layout()
    row.insertWidget(max(0, row.count() - 1), self.model_selector)


def _init_with_operational_modules(self: BingoMainWindow) -> None:
    _original_init(self)
    self._finalized = False
    self.cartons_window = None
    self.generator_window = None
    self.sales_window = None
    self.verification_window = None
    self.reports_window = None
    self.settings_window = None
    self.history_repository = SQLiteGameHistoryRepository(database_path())
    self.history_service = GameHistoryService(self.history_repository)
    self.history_game_id = None
    _install_model_selector(self)
    settings = SettingsService(application_data_dir() / "settings.json")
    self.tv_sync_server = GameSyncServer(host="0.0.0.0", port=int(settings.get("tv_server_port", 8765)))
    self.tv_sync_thread = threading.Thread(target=self.tv_sync_server.serve_forever, daemon=True)
    self.tv_sync_thread.start()
    self.tv_sync_client = GameSyncClient(str(settings.get("tv_server_host", "127.0.0.1")), int(settings.get("tv_server_port", 8765)))
    self.open_cartons = lambda: _open_cartons(self)
    self.open_sales = lambda: _open_sales(self)
    self.open_verification = lambda: _open_verification(self)
    self.open_reports = lambda: _open_reports(self)
    self.open_settings = lambda: _open_settings(self)
    self.open_tv = lambda: _open_tv(self)
    self.enter_ball = lambda: _enter_ball_with_history(self)
    self.draw_number = lambda: _draw_with_history(self)
    self.call_number = lambda number: _call_with_history(self, number)
    self.undo_number = lambda: _undo_with_history(self)
    self.toggle_pause = lambda: _pause_with_history(self)
    self.finalize_game = lambda: _finalize_game_with_history(self)
    self.new_game = lambda: _new_game_with_history(self)
    _start_history_game(self)
    wire_operational_controls(self)
    for button in self.findChildren(QPushButton):
        if button.text().startswith("▣  GENERADOR") or button.text().startswith("▣ GENERADOR"):
            button.setText("🛒  CARTONES\nGenerador · Imprimir · Ver · Diseñar")
            _replace_signal_connection(button.clicked, self.open_cartons)
        elif button.text().startswith("🛒  VENTAS") or button.text().startswith("🛒 VENTAS"):
            _replace_signal_connection(button.clicked, self.open_sales)
        elif button.text().startswith("✓  VERIFICACIÓN") or button.text().startswith("✓ VERIFICACIÓN"):
            _replace_signal_connection(button.clicked, self.open_verification)
        elif button.text().startswith("▥  REPORTES") or button.text().startswith("▥ REPORTES"):
            _replace_signal_connection(button.clicked, self.open_reports)
        elif button.text().startswith("⚙  CONFIGURACIÓN") or button.text().startswith("⚙ CONFIGURACIÓN"):
            _replace_signal_connection(button.clicked, self.open_settings)
        elif button.text().startswith("▣  PANTALLA TV") or button.text().startswith("▣ PANTALLA TV"):
            _replace_signal_connection(button.clicked, self.open_tv)
        elif button.text().startswith("■ FINALIZAR"):
            button.setProperty("fb_bingo_finish_button", True)
            _replace_signal_connection(button.clicked, self.finalize_game)
    _install_operator_shortcuts(self)

BingoMainWindow.__init__ = _init_with_operational_modules


def run_tv_mode() -> int:
    """Ejecuta únicamente la pantalla pública en una segunda computadora."""
    app = QApplication(sys.argv)
    settings = SettingsService(application_data_dir() / "settings.json")
    window = TVWindow()
    client = GameSyncClient(str(settings.get("tv_server_host", "127.0.0.1")), int(settings.get("tv_server_port", 8765)))
    timer = QTimer(window)
    def poll() -> None:
        try:
            state = client.get_state()
            window.update_game(state.get("current"), tuple(state.get("history", []))[:5])
            window.status.setText(f"FB-BINGO · {state.get('status', 'EN CURSO')} · {state.get('game', 'PARTIDA RÁPIDA')}")
        except (OSError, ValueError, TimeoutError):
            window.status.setText("FB-BINGO · ESPERANDO CONEXIÓN CON PC PRINCIPAL")
    timer.timeout.connect(poll)
    timer.start(500)
    window.showFullScreen()
    poll()
    return app.exec()


def main() -> int:
    if "--tv" in sys.argv:
        return run_tv_mode()
    app = QApplication(sys.argv)
    window = BingoMainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
