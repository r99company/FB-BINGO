from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from app.cards import BingoCard, BingoSeries, CardModel


class SQLiteSeriesRepository:
    """Persistencia local de series y matrices exactas de cartones."""

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
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS series (
                    series_id TEXT PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS cards (
                    serial TEXT PRIMARY KEY,
                    series_id TEXT NOT NULL,
                    card_index INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    grid_json TEXT NOT NULL,
                    FOREIGN KEY(series_id) REFERENCES series(series_id)
                );
                CREATE INDEX IF NOT EXISTS idx_cards_series ON cards(series_id);
                CREATE INDEX IF NOT EXISTS idx_cards_human_number ON cards(CAST(substr(serial, -6) AS INTEGER));
                """
            )

    @staticmethod
    def _series_key(series_id: str) -> str:
        value = str(series_id).strip()
        if not value:
            raise KeyError("Identificador de serie vacío")
        return f"{int(value):04d}" if value.isdigit() else value

    @staticmethod
    def _card_number(serial: str) -> int:
        value = str(serial).strip()
        if not value:
            raise KeyError("Número de cartón vacío")
        if value.isdigit():
            number = int(value)
            if number < 1:
                raise KeyError(f"Número de cartón inválido: {value}")
            return number
        suffix = value[-6:]
        if suffix.isdigit():
            return int(suffix)
        raise KeyError(f"Número de cartón inválido: {value}")

    @staticmethod
    def _card_from_row(row: sqlite3.Row) -> BingoCard:
        return BingoCard(
            serial=row["serial"],
            model=CardModel(row["model"]),
            grid=tuple(tuple(value for value in line) for line in json.loads(row["grid_json"])),
        )

    def save(self, series: BingoSeries) -> None:
        key = self._series_key(series.series_id)
        if len(series.cards) != 6:
            raise ValueError("Una serie debe contener exactamente 6 cartones")
        with self._connect() as db:
            try:
                db.execute("INSERT INTO series(series_id) VALUES (?)", (key,))
                db.executemany(
                    """
                    INSERT INTO cards(serial, series_id, card_index, model, grid_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (card.serial, key, index, card.model.value, json.dumps(card.grid))
                        for index, card in enumerate(series.cards)
                    ],
                )
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise ValueError(f"La serie '{series.series_id}' ya existe o contiene seriales repetidos") from exc

    def get(self, series_id: str) -> BingoSeries:
        key = self._series_key(series_id)
        with self._connect() as db:
            rows = db.execute(
                "SELECT serial, model, grid_json FROM cards WHERE series_id = ? ORDER BY card_index",
                (key,),
            ).fetchall()
        if len(rows) != 6:
            raise KeyError(f"Serie no encontrada: {series_id}")
        cards = tuple(self._card_from_row(row) for row in rows)
        result_id = int(series_id) if isinstance(series_id, int) else key
        return BingoSeries(series_id=result_id, cards=cards)

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
        """Load an arbitrary consecutive card range for printing/reprinting."""
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
        cards = tuple(self._card_from_row(row) for row in rows)
        expected = end_card - start_card + 1
        if len(cards) != expected:
            raise KeyError(f"No están disponibles todos los cartones {start_card}-{end_card}")
        return cards

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
        return str(row["series_id"]), int(row["card_index"]) + 1

    def get_series_id_for_card(self, serial: str) -> str:
        series_id, _ = self.get_card_position(serial)
        return series_id

    def list_series(self) -> list[BingoSeries]:
        with self._connect() as db:
            rows = db.execute("SELECT series_id FROM series ORDER BY series_id").fetchall()
        return [self.get(str(row["series_id"])) for row in rows]

    def get_grid_signatures(self) -> set[str]:
        """Return exact grid JSON signatures already persisted.

        This is intentionally a read-only uniqueness index in Python rather
        than a DB UNIQUE constraint, so old printed data can remain immutable
        even if an older database contains a duplicated layout.
        """
        with self._connect() as db:
            rows = db.execute("SELECT grid_json FROM cards").fetchall()
        return {str(row["grid_json"]) for row in rows}

    def get_recent_cards(self, limit: int = 60) -> tuple[BingoCard, ...]:
        """Load the most recently numbered cards for visual anti-repetition checks."""
        if limit < 1:
            return ()
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT serial, model, grid_json
                FROM cards
                ORDER BY CAST(substr(serial, -6) AS INTEGER) DESC
                LIMIT ?
                """,
                (int(limit),),
            ).fetchall()
        return tuple(self._card_from_row(row) for row in rows)

    def count_cards(self) -> int:
        with self._connect() as db:
            row = db.execute("SELECT COUNT(*) AS total FROM cards").fetchone()
        return int(row["total"])

    def count_series(self) -> int:
        with self._connect() as db:
            row = db.execute("SELECT COUNT(*) AS total FROM series").fetchone()
        return int(row["total"])
