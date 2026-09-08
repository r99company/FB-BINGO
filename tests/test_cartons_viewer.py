from app.ui.cartons_window import CardViewer


def test_viewer_normalizes_numeric_serials():
    assert CardViewer._normalise_serial("000025") == "25"
    assert CardViewer._normalise_serial("25") == "25"
    assert CardViewer._normalise_serial(" 000025 ") == "25"
    assert CardViewer._normalise_serial("ABC-25") == "ABC-25"
