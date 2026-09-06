from __future__ import annotations

import sys

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton

from app.settings.paths import database_path
from app.ui.main_window import BingoMainWindow
from app.ui.sales_window import SalesWindow


_original_init = BingoMainWindow.__init__


def _open_sales(self: BingoMainWindow) -> None:
    if getattr(self, "sales_window", None) is None:
        self.sales_window = SalesWindow(database_path())
        self.sales_window.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose, False)
    self.sales_window.show()
    self.sales_window.raise_()
    self.sales_window.activateWindow()


def _init_with_sales(self: BingoMainWindow) -> None:
    _original_init(self)
    self.sales_window = None
    self.open_sales = lambda: _open_sales(self)
    for button in self.findChildren(QPushButton):
        if button.text().startswith("🛒  VENTAS"):
            button.clicked.connect(self.open_sales)
            break


BingoMainWindow.__init__ = _init_with_sales


def main() -> int:
    app = QApplication(sys.argv)
    window = BingoMainWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
