from __future__ import annotations

import os
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from PySide6.QtWidgets import QApplication

from app.cards import CardModel
from app.cards.generator import SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.ui.verification_window import VerificationWindow
from app.verification import VerificationService


def test_verification_highlights_only_called_numbers_in_exact_card_grid(tmp_path):
    app = QApplication.instance() or QApplication([])
    repo = SQLiteSeriesRepository(tmp_path / "bingo.db")
    series = SeriesGenerator(seed=77).generate("0001", CardModel.A, serial_start=12500)
    repo.save(series)
    card = repo.get_card("12500")
    called = set(list(card.numbers)[:3])

    window = VerificationWindow(
        verification_service=VerificationService(repo),
        called_numbers=called,
        expected_model=CardModel.A,
    )
    window.serial_input.setText("12500")
    result = window.verify()

    assert result is not None
    svg = window.card_preview.property("svg_content")
    assert isinstance(svg, str)
    assert svg.count('class="called-number"') == 3
    assert "VERIFICACIÓN" in window.windowTitle().upper()
    window.close()
    app.processEvents()
