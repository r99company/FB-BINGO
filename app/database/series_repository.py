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
                """
            )

    def save(self, series: BingoSeries) -> None:
        with self._connect() as db:
            try:
                db.execute("INSERT INTO series(series_id) VALUES (?)", (series.series_id,))
                db.executemany(
                    """
                    INSERT INTO cards(serial, series_id, card_index, model, grid_json)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    [
                        (card.serial, series.series_id, index, card.model.value, json.dumps(card.grid))
                        for index, card in enumerate(series.cards)
                    ],
                )
            except sqlite3.IntegrityError as exc:
                db.rollback()
                raise ValueError(f"La serie '{series.series_id}' ya existe o contiene seriales repetidos") from exc

    def get(self, series_id: str) -> BingoSeries:
        with self._connect() as db:
            rows = db.execute(
                "SELECT serial, model, grid_json FROM cards WHERE series_id = ? ORDER BY card_index",
                (series_id,),
            ).fetchall()
        if len(rows) != 6:
            raise KeyError(f"Serie no encontrada: {series_id}")
        cards = tuple(
            BingoCard(
                serial=row["serial"],
                model=CardModel(row["model"]),
                grid=tuple(tuple(value for value in line) for line in json.loads(row["grid_json"])),
            )
            for row in rows
        )
        return BingoSeries(series_id=series_id, cards=cards)

    def get_card(self, serial: str) -> BingoCard:
        with self._connect() as db:
            row = db.execute(
                "SELECT serial, model, grid_json FROM cards WHERE serial = ?",
                (serial,),
            ).fetchone()
        if row is None:
            raise KeyError(f"Cartón no encontrado: {serial}")
        return BingoCard(
            serial=row["serial"],
            model=CardModel(row["model"]),
            grid=tuple(tuple(value for value in line) for line in json.loads(row["grid_json"])),
        )

    def get_card_position(self, serial: str) -> tuple[str, int]:
        """Devuelve la serie y posición humana (1..6) de un cartón."""
        with self._connect() as db:
            row = db.execute(
                "SELECT series_id, card_index FROM cards WHERE serial = ?",
                (serial.strip(),),
            ).fetchone()
        if row is None:
            raise KeyError(f"Cartón no encontrado: {serial}")
        return str(row["series_id"]), int(row["card_index"]) + 1

    def get_series_id_for_card(self, serial: str) -> str:
        series_id, _ = self.get_card_position(serial)
        return series_id
