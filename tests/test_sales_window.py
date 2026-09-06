from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.sales_window import SalesWindow


def test_sales_window_registers_carton(qtbot, tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    window = SalesWindow(tmp_path / "fb-bingo.db")
    qtbot.addWidget(window)
    window.serial_input.setText("C-00047")
    window.seller_input.setText("Vendedor 1")
    window.register_sale()
    assert "REGISTRADA" in window.feedback.text()
    assert window.sales_service.is_sold("C-00047")


def test_sales_window_blocks_duplicate(qtbot, tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    window = SalesWindow(tmp_path / "fb-bingo.db")
    qtbot.addWidget(window)
    window.serial_input.setText("C-00047")
    window.register_sale()
    window.serial_input.setText("C-00047")
    window.register_sale()
    assert "YA FUE VENDIDO" in window.feedback.text()
