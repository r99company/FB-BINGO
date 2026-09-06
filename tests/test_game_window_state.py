from app.ui.game_window import GameDisplayState


def test_recent_keeps_latest_five_in_call_order() -> None:
    state = GameDisplayState((1, 2, 3, 4, 5, 6, 7))
    assert state.recent == (3, 4, 5, 6, 7)


def test_remaining_is_based_on_unique_called_numbers() -> None:
    state = GameDisplayState((4, 18, 55))
    assert state.remaining == 87
