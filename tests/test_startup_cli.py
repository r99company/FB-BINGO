from __future__ import annotations

from app.ui.main import main


def test_main_supports_test_mode(capsys):
    result = main(["--test"])

    captured = capsys.readouterr().out
    assert result == 0
    assert "FB-BINGO OK" in captured
    assert "bola_actual=None" in captured
    assert "series_en_bd=" in captured
