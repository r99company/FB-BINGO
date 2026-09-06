from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.game_window import GameWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = GameWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
