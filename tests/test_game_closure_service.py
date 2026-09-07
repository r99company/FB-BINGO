from pathlib import Path

from app.bingo import BingoGame
from app.database.game_repository import SQLiteGameHistoryRepository
from app.services.game_closure import GameClosureService


def test_close_finishes_persisted_game_and_exports_excel(tmp_path: Path):
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    game = BingoGame(seed=11)
    game_id = repository.start_game(game_name="PARTIDA RÁPIDA", series_id="SERIE-001")
    game.call_manual(27)
    game.call_manual(81)

    service = GameClosureService(repository, tmp_path / "reports")
    output = service.close(game_id, game, game_name="PARTIDA RÁPIDA", series_id="SERIE-001")

    saved = repository.get_game(game_id)
    assert saved["status"] == "finalizada"
    assert saved["called_numbers"] == (27, 81)
    assert output.exists()
    assert output.suffix == ".xlsx"


def test_close_can_finalize_a_game_without_called_balls(tmp_path: Path):
    repository = SQLiteGameHistoryRepository(tmp_path / "bingo.db")
    game = BingoGame(seed=3)
    game_id = repository.start_game(game_name="PARTIDA RÁPIDA", series_id="SERIE-002")

    service = GameClosureService(repository, tmp_path / "reports")
    output = service.close(game_id, game, game_name="PARTIDA RÁPIDA", series_id="SERIE-002")

    assert repository.get_game(game_id)["status"] == "finalizada"
    assert repository.get_game(game_id)["called_numbers"] == ()
    assert output.exists()
