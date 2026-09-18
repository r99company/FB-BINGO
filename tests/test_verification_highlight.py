from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.cards import CardModel
from app.cards.generator import SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService


def _window(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = SQLiteSeriesRepository(tmp_path / "bingo.db")
    series = SeriesGenerator(seed=77).generate("0001", CardModel.A, serial_start=12500)
    repo.save(series)
    card = repo.get_card("12500")
    service = VerificationService(repo)
    return app, repo, card, VerificationWindow(
        verification_service=service,
        called_numbers=set(),
        expected_model=CardModel.A,
    )


def test_verification_highlights_only_called_numbers_in_exact_card_grid(tmp_path):
    app, _, card, window = _window(tmp_path)
    called = set(list(card.numbers)[:3])
    window.called_numbers = called
    window.serial_input.setText(card.serial)

    result = window.verify()

    assert result is not None
    svg = window.card_preview.property("svg_content")
    assert isinstance(svg, str)
    assert svg.count('class="called-number"') == 3
    assert f"Modelo: {card.model.value}" in window.detail_label.text()
    window.close()
    app.processEvents()


def test_verification_reports_bingo_when_all_fifteen_numbers_are_called(tmp_path):
    app, _, card, window = _window(tmp_path)
    window.called_numbers = set(card.numbers)
    window.serial_input.setText(card.serial)

    result = window.verify()

    assert result is not None
    assert result.bingo is True
    assert result.line_rows == (0, 1, 2)
    assert "BINGO" in window.result_label.text()
    assert "LOS 15 NÚMEROS" in window.prize_detail_label.text()
    window.close()
    app.processEvents()


def test_verification_reports_no_prize_when_no_row_is_complete(tmp_path):
    app, _, card, window = _window(tmp_path)
    window.called_numbers = set()
    window.serial_input.setText(card.serial)

    result = window.verify()

    assert result is not None
    assert result.bingo is False
    assert result.line_rows == ()
    assert "NO HAY LÍNEA" in window.result_label.text()
    assert "NO HAY BINGO" in window.prize_detail_label.text()
    window.close()
    app.processEvents()
