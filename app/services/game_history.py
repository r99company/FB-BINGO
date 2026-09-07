from __future__ import annotations

from app.bingo import BingoGame
from app.database.game_repository import SQLiteGameHistoryRepository


class GameHistoryService:
    """Coordina el estado vivo de Bingo con su historial persistente."""

    def __init__(self, repository: SQLiteGameHistoryRepository) -> None:
        self.repository = repository

    def start(self, game: BingoGame, *, game_name: str, series_id: str) -> int:
        return self.repository.start_game(game_name=game_name, series_id=series_id)

    def sync(self, game_id: int, game: BingoGame) -> None:
        status = "pausada" if game.state.paused else "en_curso"
        self.repository.update_game(
            game_id,
            called_numbers=game.history,
            status=status,
        )

    def finish(self, game_id: int, game: BingoGame) -> None:
        self.repository.finish_game(game_id, called_numbers=game.history)
