from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.database.series_repository import SQLiteSeriesRepository


@dataclass(frozen=True)
class Sale:
    serial: str
    sale_type: str
    seller: str = ""
    sold_at: str = ""


class SalesService:
    """Control de ventas reales, validando cartones/series generados."""

    def __init__(self, database_path: str | Path, repository: SQLiteSeriesRepository | None = None) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
        self.repository = repository
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.database_path)
        db.row_factory = sqlite3.Row
        return db

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """CREATE TABLE IF NOT EXISTS sales (
                    serial TEXT PRIMARY KEY,
                    sale_type TEXT NOT NULL CHECK(sale_type IN ('carton','serie')),
                    seller TEXT NOT NULL DEFAULT '',
                    sold_at TEXT NOT NULL
                )"""
            )
            db.execute("CREATE INDEX IF NOT EXISTS idx_sales_sold_at ON sales(sold_at)")

    def sell(self, serial: str, sale_type: str = "carton", seller: str = "") -> Sale:
        if sale_type == "carton":
            return self.sell_card(serial, seller=seller)
        if sale_type == "serie":
            return self.sell_series(serial, seller=seller)
        raise ValueError("Tipo de venta inválido")

    def sell_card(self, serial: str, seller: str = "") -> Sale:
        serial = serial.strip()
        if not serial:
            raise ValueError("Debe indicar el número o serial")
        if self.repository is not None:
            try:
                self.repository.get_card(serial)
                series_id = self.repository.get_series_id_for_card(serial)
            except KeyError as exc:
                raise ValueError(f"El cartón '{serial}' no existe en las series generadas") from exc
            if self.is_series_sold(series_id):
                raise ValueError(f"La serie '{series_id}' ya fue vendida completa")
        return self._record(serial, "carton", seller)

    def sell_series(self, series_id: str, seller: str = "") -> Sale:
        series_id = series_id.strip()
        if not series_id:
            raise ValueError("Debe indicar el número o identificador de serie")
        if self.repository is not None:
            try:
                series = self.repository.get(series_id)
            except KeyError as exc:
                raise ValueError(f"La serie '{series_id}' no existe en las series generadas") from exc
            if self.is_series_sold(series_id):
                raise ValueError(f"La serie '{series_id}' ya fue vendida")
            serials = tuple(card.serial for card in series.cards)
            with self._connect() as db:
                placeholders = ",".join("?" for _ in serials)
                row = db.execute(
                    f"SELECT 1 FROM sales WHERE sale_type = 'carton' AND serial IN ({placeholders}) LIMIT 1",
                    serials,
                ).fetchone()
            if row is not None:
                raise ValueError(f"La serie '{series_id}' no puede venderse completa: hay cartones ya fueron vendidos")
        return self._record(series_id, "serie", seller)

    def _record(self, serial: str, sale_type: str, seller: str) -> Sale:
        sold_at = datetime.now().isoformat(timespec="seconds")
        try:
            with self._connect() as db:
                db.execute(
                    "INSERT INTO sales(serial, sale_type, seller, sold_at) VALUES (?, ?, ?, ?)",
                    (serial, sale_type, seller.strip(), sold_at),
                )
        except sqlite3.IntegrityError as exc:
            raise ValueError(f"El {sale_type} '{serial}' ya fue vendido") from exc
        return Sale(serial, sale_type, seller.strip(), sold_at)

    def is_sold(self, serial: str) -> bool:
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM sales WHERE serial = ?", (serial.strip(),)).fetchone()
        return row is not None

    def is_card_sold(self, serial: str) -> bool:
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM sales WHERE serial = ? AND sale_type = 'carton'", (serial.strip(),)).fetchone()
        return row is not None

    def is_series_sold(self, series_id: str) -> bool:
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM sales WHERE serial = ? AND sale_type = 'serie'", (series_id.strip(),)).fetchone()
        return row is not None

    def list_sales(self) -> list[Sale]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT serial, sale_type, seller, sold_at FROM sales ORDER BY sold_at DESC"
            ).fetchall()
        return [Sale(row["serial"], row["sale_type"], row["seller"], row["sold_at"]) for row in rows]
