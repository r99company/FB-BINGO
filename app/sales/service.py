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


@dataclass(frozen=True)
class SalesSummary:
    """Resumen de ventas para caja y reportes."""

    total: int
    cards: int
    series: int
    by_seller: tuple[tuple[str, int], ...] = ()


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
            db.execute("CREATE INDEX IF NOT EXISTS idx_sales_type ON sales(sale_type)")

    @staticmethod
    def _series_key(series_id: str) -> str:
        value = str(series_id).strip()
        if value.isdigit():
            return f"{int(value):04d}"
        return value

    def sell(self, serial: str, sale_type: str = "carton", seller: str = "") -> Sale:
        if sale_type == "carton":
            return self.sell_card(serial, seller=seller)
        if sale_type == "serie":
            return self.sell_series(serial, seller=seller)
        raise ValueError("Tipo de venta inválido")

    def sell_card(self, serial: str, seller: str = "") -> Sale:
        entered = serial.strip()
        if not entered:
            raise ValueError("Debe indicar el número o serial")
        canonical = entered
        if self.repository is not None:
            try:
                card = self.repository.get_card(entered)
                canonical = card.serial
                series_id = self.repository.get_series_id_for_card(entered)
            except KeyError as exc:
                raise ValueError(f"El cartón '{entered}' no existe en las series generadas") from exc
            if self.is_series_sold(series_id):
                raise ValueError(f"La serie '{series_id}' ya fue vendida completa")
        return self._record(canonical, "carton", seller)

    def sell_series(self, series_id: str, seller: str = "") -> Sale:
        entered = series_id.strip()
        if not entered:
            raise ValueError("Debe indicar el número o identificador de serie")
        canonical = self._series_key(entered)
        if self.repository is not None:
            try:
                series = self.repository.get(canonical)
            except KeyError as exc:
                raise ValueError(f"La serie '{entered}' no existe en las series generadas") from exc
            if self.is_series_sold(canonical):
                raise ValueError(f"La serie '{canonical}' ya fue vendida")
            serials = tuple(card.serial for card in series.cards)
            with self._connect() as db:
                placeholders = ",".join("?" for _ in serials)
                row = db.execute(
                    f"SELECT 1 FROM sales WHERE sale_type = 'carton' AND serial IN ({placeholders}) LIMIT 1",
                    serials,
                ).fetchone()
            if row is not None:
                raise ValueError(f"La serie '{canonical}' no puede venderse completa: hay cartones ya vendidos")
        return self._record(canonical, "serie", seller)

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
        value = serial.strip()
        if self.repository is not None:
            try:
                value = self.repository.get_card(value).serial
            except KeyError:
                value = self._series_key(value)
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM sales WHERE serial = ?", (value,)).fetchone()
        return row is not None

    def is_card_sold(self, serial: str) -> bool:
        value = serial.strip()
        if self.repository is not None:
            try:
                value = self.repository.get_card(value).serial
            except KeyError:
                pass
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM sales WHERE serial = ? AND sale_type = 'carton'", (value,)).fetchone()
        return row is not None

    def is_series_sold(self, series_id: str) -> bool:
        value = self._series_key(series_id)
        with self._connect() as db:
            row = db.execute("SELECT 1 FROM sales WHERE serial = ? AND sale_type = 'serie'", (value,)).fetchone()
        return row is not None

    def list_sales(self) -> list[Sale]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT serial, sale_type, seller, sold_at FROM sales ORDER BY sold_at DESC"
            ).fetchall()
        return [Sale(row["serial"], row["sale_type"], row["seller"], row["sold_at"]) for row in rows]

    def summary(self) -> SalesSummary:
        """Devuelve un resumen consistente con la tabla real de ventas."""
        with self._connect() as db:
            totals = db.execute(
                "SELECT COUNT(*) AS total, "
                "SUM(CASE WHEN sale_type='carton' THEN 1 ELSE 0 END) AS cards, "
                "SUM(CASE WHEN sale_type='serie' THEN 1 ELSE 0 END) AS series "
                "FROM sales"
            ).fetchone()
            sellers = db.execute(
                "SELECT seller, COUNT(*) AS count FROM sales "
                "GROUP BY seller ORDER BY count DESC, seller ASC"
            ).fetchall()
        return SalesSummary(
            total=int(totals["total"] or 0),
            cards=int(totals["cards"] or 0),
            series=int(totals["series"] or 0),
            by_seller=tuple((str(row["seller"] or "SIN VENDEDOR"), int(row["count"])) for row in sellers),
        )
