from pathlib import Path

from PySide6.QtCore import QEvent, Qt
from PySide6.QtGui import QKeyEvent
from PySide6.QtWidgets import QApplication, QMessageBox

from app.cards import CardModel
from app.database.repository import SQLiteSeriesRepository
from app.production.service import ProductionService
from app.printing.layout import PrintStyle
from app.printing.modern_svg_renderer import ModernA4SvgRenderer
from app.ui.main import BingoMainWindow
from app.ui.generator_window import GeneratorWidget


def test_modern_renderer_has_qr_zone_and_serials():
    series = SeriesGenerator(seed=7).generate("12", CardModel.A, 1)
    renderer = ModernA4SvgRenderer(style=PrintStyle(show_model=False, show_serial=True, show_qr_zone=True))
    svg = renderer.render(series.cards)
    assert "11534" not in svg
    assert "FB-BINGO" in svg
    assert "CARTÓN" in svg
    assert "BINGO DE 90 BOLAS" in svg


def test_modern_renderer_can_print_without_qr_zone():
    series = SeriesGenerator(seed=8).generate("13", CardModel.A, 7)
    renderer = ModernA4SvgRenderer(style=PrintStyle(show_model=False, show_qr_zone=False))
    svg = renderer.render(series.cards)
    assert "FB-BINGO" in svg


def test_f4_yes_starts_a_clean_new_game(monkeypatch):
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    window.draw_number()
    assert window.game.history

    monkeypatch.setattr(QMessageBox, "question", lambda *args, **kwargs: QMessageBox.StandardButton.Yes)
    event = QKeyEvent(QEvent.Type.KeyPress, Qt.Key.Key_F4, Qt.KeyboardModifier.NoModifier)
    QApplication.sendEvent(window, event)

    assert window._finalized is False
    assert window.game.history == ()
    assert window.game.current_number is None
    assert window.ball_input.isEnabled()
    assert window.header_values[1].text() == "EN ESPERA"
    window.close()
    app.processEvents()


def test_generator_navigation_opens_generator_window():
    app = QApplication.instance() or QApplication([])
    window = BingoMainWindow()
    button = next(b for b in window.findChildren(QPushButton) if "GENERADOR" in b.text())
    button.click()
    assert window.generator_window is not None
    window.close()
    app.processEvents()
