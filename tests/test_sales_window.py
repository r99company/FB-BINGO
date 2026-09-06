from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.ui.sales_window import SalesWindow


def test_sales_window_registers_carton(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    window = SalesWindow(tmp_path / "fb-bingo.db")
    window.serial_input.setText("C-00047")
    window.seller_input.setText("Vendedor 1")
    assert window.register_sale() is True
    assert "REGISTRADA" in window.feedback.text()
    assert window.sales_service.is_sold("C-00047")
    window.close()


def test_sales_window_blocks_duplicate(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    window = SalesWindow(tmp_path / "fb-bingo.db")
    window.serial_input.setText("C-00047")
    assert window.register_sale() is True
    window.serial_input.setText("C-00047")
    assert window.register_sale() is False
    assert "YA FUE VENDIDO" in window.feedback.text()
    window.close()
