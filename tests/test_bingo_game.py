import pytest

from app.bingo import BingoGame, GameFinishedError, GamePausedError, GameState


def test_draws_all_90_numbers_without_repetition() -> None:
    game = BingoGame(seed=42)

    drawn = [game.draw() for _ in range(90)]

    assert len(drawn) == 90
    assert set(drawn) == set(range(1, 91))
    assert game.state.finished
    with pytest.raises(GameFinishedError):
        game.draw()


def test_current_history_and_last_five_follow_draw_order() -> None:
    game = BingoGame(seed=7)
    drawn = [game.draw() for _ in range(7)]

    assert game.current_number == drawn[-1]
    assert game.history == tuple(drawn)
    assert game.last_five == tuple(drawn[-5:])


def test_pause_and_resume_control_drawing() -> None:
    game = BingoGame(seed=1)
    first = game.draw()
    game.pause()

    assert game.state.paused
    with pytest.raises(GamePausedError):
        game.draw()

    game.resume()
    assert not game.state.paused
    assert game.draw() != first


def test_reset_starts_a_clean_game_and_is_deterministic() -> None:
    first_game = BingoGame(seed=123)
    first_game.draw()
    first_game.reset()

    second_game = BingoGame(seed=123)
    assert first_game.state.drawn_numbers == ()
    assert first_game.state.remaining_numbers == second_game.state.remaining_numbers
    assert first_game.draw() == second_game.draw()


def test_state_can_be_serialized_and_restored() -> None:
    game = BingoGame(seed=99)
    [game.draw() for _ in range(4)]
    game.pause()
    saved = game.state.to_dict()

    restored = BingoGame.from_state(GameState.from_dict(saved))
    assert restored.state == game.state
    assert restored.last_five == game.last_five
    restored.resume()
    assert restored.draw() == game.state.remaining_numbers[0]


def test_invalid_state_is_rejected() -> None:
    with pytest.raises(ValueError):
        GameState(drawn_numbers=(1, 1), remaining_numbers=tuple(range(2, 91)))


def test_ball_91_is_rejected() -> None:
    with pytest.raises(ValueError):
        GameState(drawn_numbers=(91,), remaining_numbers=tuple(range(1, 91)))


def test_restore_cannot_silently_resume_a_paused_game() -> None:
    game = BingoGame(seed=5)
    game.draw()
    game.pause()
    paused_history = game.history
    replacement = GameState(
        drawn_numbers=paused_history + (47,),
        remaining_numbers=tuple(n for n in range(1, 91) if n not in paused_history and n != 47),
        paused=False,
    )

    game.restore(replacement)

    assert game.state.paused is True
    assert game.history == paused_history + (47,)
