from app.ui.game_window import GameDisplayState


def test_display_state_shows_recent_five_in_call_order():
    state = GameDisplayState((1, 2, 3, 4, 5, 6))
    assert state.recent == (2, 3, 4, 5, 6)
    assert state.remaining == 84


def test_display_state_empty_game():
    state = GameDisplayState()
    assert state.recent == ()
    assert state.remaining == 90
