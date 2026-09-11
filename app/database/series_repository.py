from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Iterable

from app.cards import BingoCard, BingoSeries, CardModel


class SQLiteSeriesRepository:
    """Persistencia SQLite de series y cartones de FB-BINGO."""

    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self):
        db = sqlite3.connect(self.path)
        db.row_factory = sqlite3.Row
        return db

    def _init_db(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS series (
                    series_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE TABLE IF NOT EXISTS cards (
                    serial TEXT PRIMARY KEY,
                    series_id TEXT NOT NULL,
                    card_index INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    grid_json TEXT NOT NULL,
                    FOREIGN KEY(series_id) REFERENCES series(series_id)
                );
                CREATE INDEX IF NOT EXISTS idx_cards_number ON cards(serial);
                CREATE INDEX IF NOT EXISTS idx_cards_series ON cards(series_id, card_index);
                """
            )

    @staticmethod
    def _card_from_row(row: sqlite3.Row) -> BingoCard:
        return BingoCard(
            serial=str(row["serial"]),
            model=CardModel(row["model"]),
            grid=tuple(tuple(value for value in r) for r in json.loads(row["grid_json"])),
        )

    @staticmethod
    def _card_number(serial: str) -> int:
        try:
            return int(str(serial).strip().split("-")[-1])
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Serial de cartón inválido: {serial}") from exc

    def save(self, series: BingoSeries) -> None:
        with self._connect() as db:
            try:
                db.execute("INSERT INTO series(series_id) VALUES (?)", (series.series_id,))
                for index, card in enumerate(series.cards, start=1):
                    db.execute(
                        "INSERT INTO cards(serial,series_id,card_index,model,grid_json) VALUES (?,?,?,?,?)",
                        (card.serial, series.series_id, index, card.model.value, json.dumps(card.grid, separators=(",", ":"))),
                    )
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise ValueError(f"La serie o uno de sus cartones ya existe: {series.series_id}") from exc

    def get_series(self, series_id: str) -> BingoSeries:
        with self._connect() as db:
            rows = db.execute(
                "SELECT serial, model, grid_json FROM cards WHERE series_id = ? ORDER BY card_index",
                (series_id,),
            ).fetchall()
        if len(rows) != 6:
            raise KeyError(f"Serie no encontrada o incompleta: {series_id}")
        return BingoSeries(series_id=series_id, cards=tuple(self._card_from_row(row) for row in rows))

    def get_card(self, serial: str) -> BingoCard:
        number = self._card_number(serial)
        with self._connect() as db:
            row = db.execute(
                "SELECT serial, model, grid_json FROM cards WHERE serial = ? OR CAST(substr(serial, -6) AS INTEGER) = ? LIMIT 1",
                (str(serial).strip(), number),
            ).fetchone()
        if row is None:
            raise KeyError(f"Cartón no encontrado: {serial}")
        return self._card_from_row(row)

    def get_cards_range(self, start_card: int, end_card: int) -> tuple[BingoCard, ...]:
        """Carga un rango existente para imprimir o previsualizar.

        Un rango todavía no generado devuelve una tupla vacía; así las pantallas
        de producción pueden abrirse con una biblioteca nueva y mostrar
        "0 disponibles". Los flujos que exigen el rango completo validan la
        longitud después de esta consulta y producen su mensaje específico.
        """
        if start_card < 1 or end_card < start_card:
            raise ValueError("El rango de cartones no es válido")
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT serial, model, grid_json
                FROM cards
                WHERE CAST(substr(serial, -6) AS INTEGER) BETWEEN ? AND ?
                ORDER BY CAST(substr(serial, -6) AS INTEGER)
                """,
                (start_card, end_card),
            ).fetchall()
        return tuple(self._card_from_row(row) for row in rows)

    def get_card_position(self, serial: str) -> tuple[str, int]:
        """Devuelve la serie y posición humana (1..6) de un cartón."""
        number = self._card_number(serial)
        with self._connect() as db:
            row = db.execute(
                "SELECT series_id, card_index FROM cards WHERE serial = ? OR CAST(substr(serial, -6) AS INTEGER) = ? LIMIT 1",
                (str(serial).strip(), number),
            ).fetchone()
        if row is None:
            raise KeyError(f"Cartón no encontrado: {serial}")
        return str(row["series_id"]), int(row["card_index"])

    def get_grid_signatures(self) -> set[str]:
        with self._connect() as db:
            rows = db.execute("SELECT grid_json FROM cards").fetchall()
        return {str(row["grid_json"]) for row in rows}

    def get_recent_cards(self, limit: int = 60) -> tuple[BingoCard, ...]:
        if limit <= 0:
            return ()
        with self._connect() as db:
            rows = db.execute(
                "SELECT serial, model, grid_json FROM cards ORDER BY CAST(substr(serial, -6) AS INTEGER) DESC LIMIT ?",
                (limit,),
            ).fetchall()
        rows.reverse()
        return tuple(self._card_from_row(row) for row in rows)

    def next_free_series_start(self, max_cards: int, series_size: int = 6) -> int:
        if max_cards < series_size:
            raise ValueError("La capacidad no permite una serie completa")
        with self._connect() as db:
            rows = db.execute("SELECT serial FROM cards").fetchall()
        used = {self._card_number(row["serial"]) for row in rows}
        for start in range(1, max_cards - series_size + 2, series_size):
            if all(number not in used for number in range(start, start + series_size)):
                return start
        raise ValueError(f"No hay un bloque libre de {series_size} cartones hasta {max_cards:,}")
