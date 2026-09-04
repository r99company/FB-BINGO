from __future__ import annotations

import sys

from PySide6.QtWidgets import QApplication

from app.ui.generator_window import GeneratorWindow


def main() -> int:
    app = QApplication(sys.argv)
    window = GeneratorWindow()
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
