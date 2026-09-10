from PySide6.QtWidgets import QApplication

from app.cards import BingoCard, CardModel
from app.ui.designer_window import DesignerWindow


def test_designer_preview_uses_a_valid_15_number_model_a_sample():
    app = QApplication.instance() or QApplication([])
    window = DesignerWindow()

    grid = window._grid()
    card = BingoCard(serial="0001-011534", model=CardModel.A, grid=grid)

    assert len(card.numbers) == 15
    assert card.column_counts == (2, 2, 2, 2, 2, 2, 1, 1, 1)
    assert window.preview_is_real_card()
    assert window.preview_has_grid(3, 9)
    assert "MODELO A" not in window.preview_svg()

    window.close()
    app.processEvents()
