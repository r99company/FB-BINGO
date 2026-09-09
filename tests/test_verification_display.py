import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

import pytest
from PySide6.QtWidgets import QApplication

from app.cards import BingoCard, CardModel
from app.cards.generator import SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.ui.main_window import TVWindow
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


@pytest.fixture
def repository(tmp_path):
    repo = SQLiteSeriesRepository(tmp_path / "bingo.db")
    series = SeriesGenerator(seed=123).generate("0001", CardModel.A, serial_start=12_500)
    repo.save(series)
    return repo


def test_verification_shows_complete_card_and_marks_only_called_numbers(qapp, repository):
    card = repository.get_card("12500")
    first_row = set(card.row_numbers(0))
    called = set(list(first_row)[:4])
    window = VerificationWindow(
        verification_service=VerificationService(repository),
        called_numbers=called,
        expected_model=CardModel.A,
    )
    window.serial_input.setText("12500")
    result = window.verify()
    assert result is not None
    assert result.line_rows == ()
    assert result.bingo is False
    assert len(window.card_cells) == 27
    assert sum(bool(cell.property("called")) for cell in window.card_cells.values()) == 4
    assert "NO HAY LÍNEA" in window.result_label.text()
    assert "NO HAY BINGO" in window.prize_detail_label.text()
    window.close()


def test_verification_marks_full_card_as_bingo(qapp, repository):
    card = repository.get_card("12500")
    window = VerificationWindow(
        verification_service=VerificationService(repository),
        called_numbers=set(card.numbers),
        expected_model=CardModel.A,
    )
    window.serial_input.setText("12500")
    result = window.verify()
    assert result is not None and result.bingo is True
    assert sum(bool(cell.property("called")) for cell in window.card_cells.values()) == 15
    assert "BINGO" in window.result_label.text()
    window.close()


def test_verification_accepts_human_card_number_without_sale(qapp, repository):
    window = VerificationWindow(
        verification_service=VerificationService(repository),
        called_numbers=set(),
        expected_model=CardModel.A,
    )
    window.serial_input.setText("12500")
    result = window.verify()
    assert result is not None
    assert result.serial == "0001-012500"
    assert result.sold is False
    assert "NO VENDIDO" in window.detail_label.text()
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
