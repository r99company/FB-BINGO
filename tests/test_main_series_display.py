from __future__ import annotations

from app.ui.main_window import BingoMainWindow


def test_sync_ui_preserves_current_series(qapp):
    window = BingoMainWindow()
    window.header_values[2].setText("SERIE 0042")
    window.call_number(12)
    assert window.header_values[2].text() == "SERIE 0042"
    window.close()
