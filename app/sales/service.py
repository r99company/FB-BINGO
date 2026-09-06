from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class Sale:
    serial: str
    sale_type: str
    seller: str = ""
    sold_at: str = ""


class SalesService:
    """Control local de cartones/series vendidos, evitando ventas duplicadas."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)
        self.database_path.parent.mkdir(parents=True, exist_ok=True)
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
        serial = serial.strip()
        if not serial:
            raise ValueError("Debe indicar el número o serial")
        if sale_type not in {"carton", "serie"}:
            raise ValueError("Tipo de venta inválido")
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

    def list_sales(self) -> list[Sale]:
        with self._connect() as db:
            rows = db.execute("SELECT serial, sale_type, seller, sold_at FROM sales ORDER BY sold_at DESC").fetchall()
        return [Sale(row["serial"], row["sale_type"], row["seller"], row["sold_at"]) for row in rows]
