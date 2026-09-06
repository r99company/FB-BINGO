import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.cards import BingoCard, CardModel
from app.ui.game_window import GameWindow


MATRIX = (
    (1, None, 21, None, 41, None, 61, None, 81),
    (None, 12, None, 32, 44, 52, None, 72, None),
    (9, None, 29, 39, None, 59, None, None, 89),
)


class FakeRepository:
    def __init__(self, card: BingoCard | None = None) -> None:
        self.card = card

    def get_card(self, serial: str) -> BingoCard:
        if self.card is None or self.card.serial != serial:
            raise KeyError(f"Cartón no encontrado: {serial}")
        return self.card


@pytest.fixture(scope="session")
def qapp():
    return QApplication.instance() or QApplication([])


def make_window(qapp):
    card = BingoCard(serial="A-000001", model=CardModel.A, grid=MATRIX)
    return GameWindow(repository=FakeRepository(card))


def test_verify_serial_reports_line(qapp):
    window = make_window(qapp)
    result = window.verify_serial(" A-000001 ", {1, 21, 41, 61, 81})

    assert result is not None
    assert result.is_line({1, 21, 41, 61, 81}) is True
    assert result.is_bingo({1, 21, 41, 61, 81}) is False
    assert window.verification_result_label.text() == "LÍNEA · Cartón A-000001 · Fila(s): 1"
    window.close()


def test_verify_serial_reports_bingo(qapp):
    window = make_window(qapp)
    card = window.repository.card
    result = window.verify_serial(card.serial, set(card.numbers))

    assert result is not None
    assert result.is_bingo(card.numbers) is True
    assert window.verification_result_label.text() == "BINGO · Cartón A-000001"
    window.close()


def test_verify_serial_reports_missing_card(qapp):
    window = make_window(qapp)
    result = window.verify_serial("NO-EXISTE", set())

    assert result is None
    assert "Cartón no encontrado" in window.verification_result_label.text()
    window.close()
