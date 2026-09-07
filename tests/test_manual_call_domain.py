from __future__ import annotations

import pytest

from app.bingo import BingoGame
from app.bingo.exceptions import GameFinishedError, GamePausedError


def test_call_manual_accepts_physical_ball_and_updates_history() -> None:
    game = BingoGame(seed=7)
    assert game.call_manual(42) == 42
    assert game.current_number == 42
    assert game.history == (42,)
    assert 42 not in game.state.remaining_numbers


def test_call_manual_rejects_duplicate_ball() -> None:
    game = BingoGame(seed=7)
    game.call_manual(42)
    with pytest.raises(ValueError, match="ya fue cantada"):
        game.call_manual(42)


def test_call_manual_rejects_ball_outside_90_ball_range() -> None:
    game = BingoGame(seed=7)
    with pytest.raises(ValueError, match="1 y 90"):
        game.call_manual(91)


def test_call_manual_rejects_when_game_is_paused() -> None:
    game = BingoGame(seed=7)
    game.pause()
    with pytest.raises(GamePausedError):
        game.call_manual(42)


def test_call_manual_rejects_when_game_is_finished() -> None:
    game = BingoGame(seed=7)
    for _ in range(90):
        game.draw()
    with pytest.raises(GameFinishedError):
        game.call_manual(42)

# Stabilization regression: keep physical-ball flow covered in CI.
