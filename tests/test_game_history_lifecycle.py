from __future__ import annotations

import pytest

from app.database.game_repository import SQLiteGameHistoryRepository


def test_start_update_and_finish_game(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")

    game_id = repository.start_game(game_name="PARTIDA RÁPIDA", series_id="SERIE-001")
    assert repository.get_game(game_id)["status"] == "en_curso"

    repository.update_game(game_id, called_numbers=(12, 44), status="en_curso")
    assert repository.get_game(game_id)["called_numbers"] == (12, 44)

    repository.finish_game(game_id, called_numbers=(12, 44, 90))
    game = repository.get_game(game_id)
    assert game["called_numbers"] == (12, 44, 90)
    assert game["status"] == "finalizada"
    assert game["finished_at"] is not None


def test_finish_game_cannot_finish_twice(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    game_id = repository.start_game(game_name="UNO", series_id="S1")
    repository.finish_game(game_id, called_numbers=(1,))

    with pytest.raises(ValueError, match="finalizada"):
        repository.finish_game(game_id, called_numbers=(1, 2))


def test_update_missing_game_raises(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    with pytest.raises(KeyError, match="Partida no encontrada"):
        repository.update_game(999, called_numbers=(1,), status="en_curso")
