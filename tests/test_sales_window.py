from pathlib import Path

from PySide6.QtWidgets import QApplication

from app.cards import CardModel, SeriesGenerator
from app.database.series_repository import SQLiteSeriesRepository
from app.ui.sales_window import SalesWindow


def prepare_series(db: Path):
    repository = SQLiteSeriesRepository(db)
    series = SeriesGenerator(seed=7).generate("S-001", model=CardModel.A, serial_start=1)
    repository.save(series)
    return series


def test_sales_window_registers_carton(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    db = tmp_path / "fb-bingo.db"
    series = prepare_series(db)
    window = SalesWindow(db)
    serial = series.cards[0].serial
    window.serial_input.setText(serial)
    window.seller_input.setText("Vendedor 1")
    assert window.register_sale() is True
    assert "REGISTRADA" in window.feedback.text()
    assert window.sales_service.is_sold(serial)
    window.close()


def test_sales_window_blocks_duplicate(tmp_path: Path):
    app = QApplication.instance() or QApplication([])
    db = tmp_path / "fb-bingo.db"
    series = prepare_series(db)
    serial = series.cards[0].serial
    window = SalesWindow(db)
    window.serial_input.setText(serial)
    assert window.register_sale() is True
    window.serial_input.setText(serial)
    assert window.register_sale() is False
    assert "YA FUE VENDIDO" in window.feedback.text()
    window.close()
