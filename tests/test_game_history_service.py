from __future__ import annotations

from app.bingo import BingoGame
from app.database.game_repository import SQLiteGameHistoryRepository
from app.services.game_history import GameHistoryService


def test_service_starts_syncs_and_finishes_game(tmp_path) -> None:
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    service = GameHistoryService(repository)
    game = BingoGame(seed=7)

    game_id = service.start(game, game_name="PARTIDA RÁPIDA", series_id="SERIE-001")
    game.call_manual(15)
    service.sync(game_id, game)

    saved = repository.get_game(game_id)
    assert saved["called_numbers"] == (15,)
    assert saved["status"] == "en_curso"

    service.finish(game_id, game)
    saved = repository.get_game(game_id)
    assert saved["status"] == "finalizada"
    assert saved["called_numbers"] == (15,)
    assert saved["finished_at"] is not None
