from __future__ import annotations

from datetime import datetime
from pathlib import Path

from app.bingo import BingoGame
from app.database.game_repository import SQLiteGameHistoryRepository
from app.reports.excel_exporter import export_game_history


class GameClosureService:
    """Cierra una partida persistida y genera su reporte Excel."""

    def __init__(
        self,
        repository: SQLiteGameHistoryRepository,
        output_dir: str | Path,
    ) -> None:
        self.repository = repository
        self.output_dir = Path(output_dir)

    def close(
        self,
        game_id: int,
        game: BingoGame,
        *,
        game_name: str,
        series_id: str,
    ) -> Path:
        self.repository.finish_game(game_id, called_numbers=game.history)
        saved = self.repository.get_game(game_id)
        finished_at = saved["finished_at"]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output = self.output_dir / f"FB-BINGO-partida-{game_id}-{timestamp}.xlsx"
        return export_game_history(
            output,
            game_name=game_name,
            series=series_id,
            called_numbers=game.history,
            finished_at=finished_at,
            status=saved["status"],
        )
