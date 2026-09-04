from app.ui.main import OperatorDisplayState


def test_operator_display_state_tracks_recent_and_counts() -> None:
    state = OperatorDisplayState((7, 12, 44, 3, 81, 20))

    assert state.current == 20
    assert state.recent == (20, 81, 3, 44, 12)
    assert state.called_count == 6
    assert state.remaining_count == 84


def test_operator_display_state_is_empty_before_first_ball() -> None:
    state = OperatorDisplayState(())

    assert state.current is None
    assert state.recent == ()
    assert state.called_count == 0
    assert state.remaining_count == 90
