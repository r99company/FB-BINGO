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

    @staticmethod
    def _validate_metadata(game_name: str, series_id: str) -> None:
        if not game_name.strip():
            raise ValueError("El nombre del juego no puede estar vacío")
        if not series_id.strip():
            raise ValueError("La serie no puede estar vacía")

    @staticmethod
    def _validate_status(status: str) -> None:
        if status not in _ALLOWED_STATUSES:
            raise ValueError("estado de partida inválido")

    @staticmethod
    def _numbers_json(called_numbers: tuple[int, ...] | list[int]) -> str:
        return json.dumps(list(called_numbers))

    def start_game(self, *, game_name: str, series_id: str) -> int:
        self._validate_metadata(game_name, series_id)
        with self._connect() as db:
            cursor = db.execute(
                """
                INSERT INTO game_history(
                    game_name, series_id, called_numbers_json, status
                ) VALUES (?, ?, ?, 'en_curso')
                """,
                (game_name.strip(), series_id.strip(), "[]"),
            )
            return int(cursor.lastrowid)

    def update_game(
        self,
        game_id: int,
        *,
        called_numbers: tuple[int, ...] | list[int],
        status: str,
    ) -> None:
        self._validate_status(status)
        with self._connect() as db:
            row = db.execute(
                "SELECT status FROM game_history WHERE game_id = ?", (game_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Partida no encontrada: {game_id}")
            if row["status"] == "finalizada":
                raise ValueError("La partida ya está finalizada")
            if status == "finalizada":
                raise ValueError("Use finish_game para finalizar la partida")
            db.execute(
                """
                UPDATE game_history
                SET called_numbers_json = ?, status = ?
                WHERE game_id = ?
                """,
                (self._numbers_json(called_numbers), status, game_id),
            )

    def finish_game(
        self,
        game_id: int,
        *,
        called_numbers: tuple[int, ...] | list[int],
    ) -> None:
        with self._connect() as db:
            row = db.execute(
                "SELECT status FROM game_history WHERE game_id = ?", (game_id,)
            ).fetchone()
            if row is None:
                raise KeyError(f"Partida no encontrada: {game_id}")
            if row["status"] == "finalizada":
                raise ValueError("La partida ya está finalizada")
            db.execute(
                """
                UPDATE game_history
                SET called_numbers_json = ?, status = 'finalizada',
                    finished_at = CURRENT_TIMESTAMP
                WHERE game_id = ?
                """,
                (self._numbers_json(called_numbers), game_id),
            )

    def save_game(
        self,
        *,
        game_name: str,
        series_id: str,
        called_numbers: tuple[int, ...] | list[int],
        status: str,
    ) -> int:
        """Guarda una partida completa; conservado para compatibilidad."""
        self._validate_status(status)
        self._validate_metadata(game_name, series_id)
        with self._connect() as db:
            finished_at = "CURRENT_TIMESTAMP" if status == "finalizada" else "NULL"
            cursor = db.execute(
                f"""
                INSERT INTO game_history(
                    game_name, series_id, called_numbers_json, status, finished_at
                ) VALUES (?, ?, ?, ?, {finished_at})
                """,
                (game_name.strip(), series_id.strip(), self._numbers_json(called_numbers), status),
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
