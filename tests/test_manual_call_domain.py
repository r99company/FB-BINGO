import pytest

from app.bingo import BingoGame, GameFinishedError, GamePausedError


def test_manual_call_accepts_physical_ball_and_updates_history():
    game = BingoGame(seed=42)
    assert game.call_manual(37) == 37
    assert game.current_number == 37
    assert game.history == (37,)
    assert 37 not in game.state.remaining_numbers


def test_manual_call_rejects_duplicate_ball():
    game = BingoGame(seed=42)
    game.call_manual(37)
    with pytest.raises(ValueError, match="ya fue cantada"):
        game.call_manual(37)


def test_manual_call_rejects_out_of_range_ball():
    game = BingoGame(seed=42)
    with pytest.raises(ValueError, match="1 y 90"):
        game.call_manual(91)


def test_manual_call_respects_pause():
    game = BingoGame(seed=42)
    game.pause()
    with pytest.raises(GamePausedError):
        game.call_manual(37)


def test_manual_call_rejects_finished_game():
    game = BingoGame(seed=42)
    for number in range(1, 91):
        game.call_manual(number)
    with pytest.raises(GameFinishedError):
        game.call_manual(1)
