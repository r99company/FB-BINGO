import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.cards import BingoCard, CardModel
from app.database import SQLiteSeriesRepository
from app.ui.main_window import TVWindow
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService


MATRIX = (
    (1, None, 21, None, 41, None, 61, None, 81),
    (None, 12, None, 32, 44, 52, None, 72, None),
    (9, None, 29, 39, None, 59, None, None, 89),
)


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def repository(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "bingo.db")
    cards = tuple(
        BingoCard(serial=f"0001-{index:06d}", model=CardModel.A, grid=MATRIX)
        for index in range(1, 7)
    )
    # A real series uses unique serials but the same matrix is sufficient for this UI test.
    from app.cards import BingoSeries
    repo.save(BingoSeries(series_id=1, cards=cards))
    return repo


def test_verification_shows_complete_card_and_marks_only_called_numbers(qapp, repository):
    window = VerificationWindow(
        verification_service=VerificationService(repository),
        called_numbers={1, 21, 41, 61},
        expected_model=CardModel.A,
    )
    window.serial_input.setText("1")

    result = window.verify()

    assert result is not None
    assert result.line_rows == ()
    assert result.bingo is False
    assert len(window.card_cells) == 27
    assert window.card_cells[(0, 0)].property("called") is True
    assert window.card_cells[(0, 4)].property("called") is True
    assert window.card_cells[(0, 8)].property("called") is False
    assert window.card_cells[(1, 1)].text() == "12"
    assert "NO HAY LÍNEA" in window.result_label.text()
    assert "NO HAY BINGO" in window.prize_detail_label.text()
    window.close()


def test_verification_marks_full_card_as_bingo(qapp, repository):
    window = VerificationWindow(
        verification_service=VerificationService(repository),
        called_numbers=set(BingoCard(serial="x", model=CardModel.A, grid=MATRIX).numbers),
        expected_model=CardModel.A,
    )
    window.serial_input.setText("1")

    result = window.verify()

    assert result is not None and result.bingo is True
    assert all(cell.property("called") is True for cell in window.card_cells.values() if cell.text())
    assert "BINGO" in window.result_label.text()
    window.close()


def test_tv_marks_all_played_numbers_and_keeps_current_distinct(qapp):
    window = TVWindow()
    window.update_game(46, (46, 68, 53, 45, 81))

    called = {46, 68, 53, 45, 81}
    assert all(window.board_buttons[n].property("called") is True for n in called)
    assert all(window.board_buttons[n].property("called") is False for n in {1, 44, 47, 90})
    assert window.board_buttons[46].property("current") is True
    assert window.count.text() == "5 / 90"
    window.close()
