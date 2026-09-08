from __future__ import annotations

import pytest

from app.cards import CardModel, SeriesGenerator
from app.verification.service import VerificationService


class FakeRepository:
    def __init__(self, cards):
        self.cards = {card.serial: card for card in cards}
        self.positions = {card.serial: ("SERIE-1", index + 1) for index, card in enumerate(cards)}

    def get_card(self, serial):
        return self.cards[serial]

    def get_card_position(self, serial):
        return self.positions[serial]


def test_verification_uses_exact_model_and_rejects_mismatch():
    series_a = SeriesGenerator(seed=101).generate("A", CardModel.A, serial_start=1)
    series_b = SeriesGenerator(seed=202).generate("B", CardModel.B, serial_start=100)
    repository = FakeRepository([series_a.cards[0], series_b.cards[0]])
    service = VerificationService(repository)

    called_a = set(series_a.cards[0].numbers)
    result_a = service.verify(series_a.cards[0].serial, called_a, expected_model=CardModel.A)
    assert result_a.model is CardModel.A
    assert result_a.bingo is True

    called_b = set(series_b.cards[0].numbers)
    result_b = service.verify(series_b.cards[0].serial, called_b, expected_model=CardModel.B)
    assert result_b.model is CardModel.B
    assert result_b.bingo is True

    with pytest.raises(ValueError, match="CARTÓN DE OTRO MODELO"):
        service.verify(series_b.cards[0].serial, called_b, expected_model=CardModel.A)


def test_model_selector_defaults_to_a_and_allows_switch_between_games(monkeypatch):
    from PySide6.QtWidgets import QApplication
    from app.ui.model_selector import GameModelSelector

    app = QApplication.instance() or QApplication([])
    selector = GameModelSelector()
    assert selector.current_model is CardModel.A

    active = {"value": False}
    selector.set_change_guard(lambda: not active["value"])
    selector.combo.setCurrentIndex(1)
    assert selector.current_model is CardModel.B

    monkeypatch.setattr("app.ui.model_selector.QMessageBox.warning", lambda *args, **kwargs: None)
    active["value"] = True
    selector.combo.setCurrentIndex(0)
    assert selector.current_model is CardModel.B

    active["value"] = False
    selector.combo.setCurrentIndex(0)
    assert selector.current_model is CardModel.A
    selector.close()
    app.quit()
