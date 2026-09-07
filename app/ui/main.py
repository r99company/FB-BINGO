from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from app.database import SQLiteGameHistoryRepository, SQLiteSeriesRepository
from app.sales import SalesService
from app.services import GameHistoryService
from app.settings.paths import database_path
from app.ui.main_window import BingoMainWindow
from app.ui.sales_window import SalesWindow
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService


_original_init = BingoMainWindow.__init__
_original_enter_ball = BingoMainWindow.enter_ball
_original_draw_number = BingoMainWindow.draw_number
_original_call_number = BingoMainWindow.call_number
_original_undo_number = BingoMainWindow.undo_number
_original_toggle_pause = BingoMainWindow.toggle_pause
_original_new_game = BingoMainWindow.new_game


def _open_sales(self: BingoMainWindow) -> None:
    if getattr(self, "sales_window", None) is None:
        self.sales_window = SalesWindow(database_path())
        self.sales_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    self.sales_window.show()
    self.sales_window.raise_()
    self.sales_window.activateWindow()


def _open_verification(self: BingoMainWindow) -> None:
    if getattr(self, "verification_window", None) is None:
        repository = SQLiteSeriesRepository(database_path())
        sales = SalesService(database_path(), repository=repository)
        service = VerificationService(repository, sales)
        self.verification_window = VerificationWindow(
            called_numbers=self.game.history,
            verification_service=service,
        )
        self.verification_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    self.verification_window.called_numbers = self.game.history
    self.verification_window.show()
    self.verification_window.raise_()
    self.verification_window.activateWindow()
    self.verification_window.serial_input.setFocus()


def _history_sync(self: BingoMainWindow) -> None:
    game_id = getattr(self, "history_game_id", None)
    if game_id is not None:
        self.history_service.sync(game_id, self.game)


def _start_history_game(self: BingoMainWindow) -> None:
    self.history_game_id = self.history_service.start(
        self.game,
        game_name=self.header_values[0].text() or "PARTIDA RÁPIDA",
        series_id=self.header_values[2].text() or "—",
    )


def _enter_ball_with_history(self: BingoMainWindow) -> bool:
    if self.game.state.paused:
        self.ball_message.setText("Ⅱ PARTIDA PAUSADA · NO SE PUEDE DIGITAR")
        self.ball_input.selectAll()
        self.ball_input.setFocus()
        return False
    result = _original_enter_ball(self)
    if result:
        _history_sync(self)
    return result


def _draw_with_history(self: BingoMainWindow) -> None:
    _original_draw_number(self)
    _history_sync(self)


def _call_with_history(self: BingoMainWindow, number: int) -> None:
    _original_call_number(self, number)
    _history_sync(self)


def _undo_with_history(self: BingoMainWindow) -> None:
    _original_undo_number(self)
    _history_sync(self)


def _pause_with_history(self: BingoMainWindow) -> None:
    _original_toggle_pause(self)
    _history_sync(self)


def _new_game_with_history(self: BingoMainWindow) -> None:
    old_game_id = getattr(self, "history_game_id", None)
    if old_game_id is not None and self.game.history:
        self.history_service.finish(old_game_id, self.game)
    _original_new_game(self)
    _start_history_game(self)


def _init_with_operational_modules(self: BingoMainWindow) -> None:
    _original_init(self)
    self.sales_window = None
    self.verification_window = None
    self.history_repository = SQLiteGameHistoryRepository(database_path())
    self.history_service = GameHistoryService(self.history_repository)
    self.history_game_id = None
    self.open_sales = lambda: _open_sales(self)
    self.open_verification = lambda: _open_verification(self)
    self.enter_ball = lambda: _enter_ball_with_history(self)
    self.draw_number = lambda: _draw_with_history(self)
    self.call_number = lambda number: _call_with_history(self, number)
    self.undo_number = lambda: _undo_with_history(self)
    self.toggle_pause = lambda: _pause_with_history(self)
    self.new_game = lambda: _new_game_with_history(self)
    _start_history_game(self)
    for button in self.findChildren(QPushButton):
        if button.text().startswith("🛒  VENTAS"):
            button.clicked.connect(self.open_sales)
        elif button.text().startswith("✓  VERIFICACIÓN"):
            button.clicked.connect(self.open_verification)


BingoMainWindow.__init__ = _init_with_operational_modules


def main() -> int:
    app = QApplication(sys.argv)
    window = BingoMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
