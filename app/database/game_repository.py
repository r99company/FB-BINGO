from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any


_ALLOWED_STATUSES = {"en_curso", "pausada", "finalizada"}


class SQLiteGameHistoryRepository:
    """Persistencia local de partidas para historial y reportes."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS game_history (
                    game_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    game_name TEXT NOT NULL,
                    series_id TEXT NOT NULL,
                    called_numbers_json TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    finished_at TEXT
                )
                """
            )

    def save_game(
        self,
        *,
        game_name: str,
        series_id: str,
        called_numbers: tuple[int, ...] | list[int],
        status: str,
    ) -> int:
        if status not in _ALLOWED_STATUSES:
            raise ValueError("estado de partida inválido")
        if not game_name.strip():
            raise ValueError("El nombre del juego no puede estar vacío")
        if not series_id.strip():
            raise ValueError("La serie no puede estar vacía")

        with self._connect() as db:
            if status == "finalizada":
                cursor = db.execute(
                    """
                    INSERT INTO game_history(
                        game_name, series_id, called_numbers_json, status, finished_at
                    ) VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (game_name.strip(), series_id.strip(), json.dumps(list(called_numbers)), status),
                )
            else:
                cursor = db.execute(
                    """
                    INSERT INTO game_history(
                        game_name, series_id, called_numbers_json, status
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (game_name.strip(), series_id.strip(), json.dumps(list(called_numbers)), status),
                )
            return int(cursor.lastrowid)

    def get_game(self, game_id: int) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM game_history WHERE game_id = ?", (game_id,)
            ).fetchone()
        if row is None:
            raise KeyError(f"Partida no encontrada: {game_id}")
        return self._row_to_dict(row)

    def list_games(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit < 1:
            raise ValueError("El límite debe ser mayor que cero")
        with self._connect() as db:
            rows = db.execute(
                "SELECT * FROM game_history ORDER BY game_id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [self._row_to_dict(row) for row in rows]

    @staticmethod
    def _row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
        result = dict(row)
        result["called_numbers"] = tuple(json.loads(result.pop("called_numbers_json")))
        return result
