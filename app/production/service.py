from __future__ import annotations

from collections.abc import Callable

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository

from .models import ProductionLot, plan_lot


class DuplicateProductionError(RuntimeError):
    """Raised when a production range would reuse an existing card/series."""


class ProductionService:
    """Coordinates validated six-card series generation and SQLite persistence."""

    def __init__(self, repository: SQLiteSeriesRepository, generator: SeriesGenerator | None = None) -> None:
        self.repository = repository
        self.generator = generator or SeriesGenerator()
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self.repository._connect() as db:  # repository owns the SQLite path/connection policy
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS production_lots (
                    lot_id INTEGER PRIMARY KEY,
                    start_card INTEGER NOT NULL,
                    end_card INTEGER NOT NULL,
                    series_count INTEGER NOT NULL,
                    model TEXT NOT NULL,
                    operator TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE UNIQUE INDEX IF NOT EXISTS idx_production_range
                    ON production_lots(start_card, end_card);
                """
            )

    def create_lot(
        self,
        start_card: int,
        end_card: int,
        model: CardModel = CardModel.A,
        operator: str = "",
    ) -> ProductionLot:
        lot = plan_lot(start_card, end_card, model=model, operator=operator)
        with self.repository._connect() as db:
            row = db.execute(
                "SELECT 1 FROM cards WHERE serial LIKE ? LIMIT 1",
                (f"%-{start_card:06d}",),
            ).fetchone()
            if row is not None:
                raise DuplicateProductionError(f"El cartón {start_card} ya existe")
            row = db.execute(
                "SELECT COALESCE(MAX(lot_id), 0) + 1 AS next_id FROM production_lots"
            ).fetchone()
            lot = ProductionLot(
                lot_id=int(row["next_id"]),
                start_card=lot.start_card,
                end_card=lot.end_card,
                series_count=lot.series_count,
                model=lot.model,
                operator=lot.operator,
                status=lot.status,
                created_at=lot.created_at,
            )
            db.execute(
                "INSERT INTO production_lots(lot_id,start_card,end_card,series_count,model,operator,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (lot.lot_id, lot.start_card, lot.end_card, lot.series_count, lot.model.value, lot.operator, lot.status, lot.created_at),
            )
        return lot

    def generate_lot(
        self,
        lot_id: int,
        progress_callback: Callable[[int], None] | None = None,
    ) -> ProductionLot:
        with self.repository._connect() as db:
            row = db.execute("SELECT * FROM production_lots WHERE lot_id = ?", (lot_id,)).fetchone()
        if row is None:
            raise KeyError(f"Lote no encontrado: {lot_id}")
        lot = ProductionLot(
            lot_id=row["lot_id"], start_card=row["start_card"], end_card=row["end_card"],
            series_count=row["series_count"], model=CardModel(row["model"]),
            operator=row["operator"], status=row["status"], created_at=row["created_at"],
        )
        total = lot.card_count
        completed = 0
        for offset in range(0, total, 6):
            first_card = lot.start_card + offset
            series_number = (first_card - 1) // 6 + 1
            series_id = f"{series_number:04d}"
            try:
                series = self.generator.generate(series_id, lot.model, serial_start=first_card)
                self.repository.save(series)
            except ValueError as exc:
                raise DuplicateProductionError(str(exc)) from exc
            completed += 6
            if progress_callback:
                progress_callback(completed)
        with self.repository._connect() as db:
            db.execute("UPDATE production_lots SET status = 'generated' WHERE lot_id = ?", (lot_id,))
        return ProductionLot(**{**lot.__dict__, "status": "generated"}) if hasattr(lot, "__dict__") else ProductionLot(
            lot_id=lot.lot_id, start_card=lot.start_card, end_card=lot.end_card,
            series_count=lot.series_count, model=lot.model, operator=lot.operator,
            status="generated", created_at=lot.created_at,
        )
