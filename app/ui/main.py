from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from app.database import SQLiteSeriesRepository
from app.sales import SalesService
from app.settings.paths import database_path
from app.ui.main_window import BingoMainWindow
from app.ui.sales_window import SalesWindow
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService


_original_init = BingoMainWindow.__init__
_original_enter_ball = BingoMainWindow.enter_ball


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


def _enter_ball_guarded(self: BingoMainWindow) -> bool:
    if self.game.state.paused:
        self.ball_message.setText("Ⅱ PARTIDA PAUSADA · NO SE PUEDE DIGITAR")
        self.ball_input.selectAll()
        self.ball_input.setFocus()
        return False
    return _original_enter_ball(self)


def _init_with_operational_modules(self: BingoMainWindow) -> None:
    _original_init(self)
    self.sales_window = None
    self.verification_window = None
    self.open_sales = lambda: _open_sales(self)
    self.open_verification = lambda: _open_verification(self)
    self.enter_ball = lambda: _enter_ball_guarded(self)
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
