from __future__ import annotations

import pytest

from app.database.game_repository import SQLiteGameHistoryRepository


def test_save_and_get_finished_game(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    game_id = repository.save_game(
        game_name="PARTIDA RÁPIDA",
        series_id="SERIE-001",
        called_numbers=(12, 44, 90),
        status="finalizada",
    )

    game = repository.get_game(game_id)

    assert game["game_id"] == game_id
    assert game["game_name"] == "PARTIDA RÁPIDA"
    assert game["series_id"] == "SERIE-001"
    assert game["called_numbers"] == (12, 44, 90)
    assert game["status"] == "finalizada"
    assert game["finished_at"] is not None


def test_list_games_returns_most_recent_first(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    first = repository.save_game(
        game_name="UNO", series_id="S1", called_numbers=(1,), status="finalizada"
    )
    second = repository.save_game(
        game_name="DOS", series_id="S2", called_numbers=(2,), status="finalizada"
    )

    games = repository.list_games()

    assert [game["game_id"] for game in games[:2]] == [second, first]


def test_rejects_invalid_status(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")

    with pytest.raises(ValueError, match="estado"):
        repository.save_game(
            game_name="UNO", series_id="S1", called_numbers=(), status="inventada"
        )
