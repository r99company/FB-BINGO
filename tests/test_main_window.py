from app.ui.main import BingoMainWindow


def test_main_module_exposes_bingo_main_window():
    assert BingoMainWindow.__name__ == "BingoMainWindow"
