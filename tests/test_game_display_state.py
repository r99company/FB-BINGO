from app.ui.game_window import GameDisplayState


def test_recent_numbers_are_last_five_in_call_order():
    state = GameDisplayState((1, 2, 3, 4, 5, 6, 7))
    assert state.recent == (3, 4, 5, 6, 7)
    assert state.remaining == 83


def test_empty_game_has_no_recent_numbers():
    state = GameDisplayState()
    assert state.recent == ()
    assert state.remaining == 90
