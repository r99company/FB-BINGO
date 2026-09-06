from __future__ import annotations

from collections.abc import Callable

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository

from .models import DEFAULT_PRODUCTION_CAPACITY, ProductionLot, plan_lot


class DuplicateProductionError(RuntimeError):
    """Raised when a production range would reuse an existing card/series."""


class ProductionService:
    """Coordinates validated six-card series generation and SQLite persistence."""

    def __init__(
        self,
        repository: SQLiteSeriesRepository,
        generator: SeriesGenerator | None = None,
        max_cards: int = DEFAULT_PRODUCTION_CAPACITY,
    ) -> None:
        if max_cards < 1:
            raise ValueError("La capacidad de producción debe ser positiva")
        self.repository = repository
        self.generator = generator or SeriesGenerator(max_serial=max_cards)
        self.max_cards = max_cards
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        with self.repository._connect() as db:
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
                CREATE INDEX IF NOT EXISTS idx_production_range
                    ON production_lots(start_card, end_card);
                """
            )

    @staticmethod
    def _lot_from_row(row) -> ProductionLot:
        return ProductionLot(
            lot_id=int(row["lot_id"]),
            start_card=int(row["start_card"]),
            end_card=int(row["end_card"]),
            series_count=int(row["series_count"]),
            model=CardModel(row["model"]),
            operator=row["operator"],
            status=row["status"],
            created_at=row["created_at"],
        )

    def create_lot(
        self,
        start_card: int,
        end_card: int,
        model: CardModel = CardModel.A,
        operator: str = "",
    ) -> ProductionLot:
        planned = plan_lot(
            start_card,
            end_card,
            model=model,
            operator=operator,
            max_cards=self.max_cards,
        )
        with self.repository._connect() as db:
            overlap = db.execute(
                """
                SELECT lot_id FROM production_lots
                WHERE start_card <= ? AND end_card >= ?
                LIMIT 1
                """,
                (planned.end_card, planned.start_card),
            ).fetchone()
            if overlap is not None:
                raise DuplicateProductionError(
                    f"El rango {planned.start_card}-{planned.end_card} se superpone al lote {overlap['lot_id']}"
                )

            existing = db.execute(
                """
                SELECT serial FROM cards
                WHERE CAST(substr(serial, -6) AS INTEGER) BETWEEN ? AND ?
                LIMIT 1
                """,
                (planned.start_card, planned.end_card),
            ).fetchone()
            if existing is not None:
                raise DuplicateProductionError(
                    f"El rango {planned.start_card}-{planned.end_card} contiene el cartón existente {existing['serial']}"
                )

            row = db.execute(
                "SELECT COALESCE(MAX(lot_id), 0) + 1 AS next_id FROM production_lots"
            ).fetchone()
            lot = ProductionLot(
                lot_id=int(row["next_id"]),
                start_card=planned.start_card,
                end_card=planned.end_card,
                series_count=planned.series_count,
                model=planned.model,
                operator=planned.operator,
                status=planned.status,
                created_at=planned.created_at,
            )
            db.execute(
                """
                INSERT INTO production_lots(
                    lot_id,start_card,end_card,series_count,model,operator,status,created_at
                ) VALUES (?,?,?,?,?,?,?,?)
                """,
                (
                    lot.lot_id,
                    lot.start_card,
                    lot.end_card,
                    lot.series_count,
                    lot.model.value,
                    lot.operator,
                    lot.status,
                    lot.created_at,
                ),
            )
        return lot

    def get_lot(self, lot_id: int) -> ProductionLot:
        with self.repository._connect() as db:
            row = db.execute("SELECT * FROM production_lots WHERE lot_id = ?", (lot_id,)).fetchone()
        if row is None:
            raise KeyError(f"Lote no encontrado: {lot_id}")
        return self._lot_from_row(row)

    def _set_status(self, lot_id: int, status: str) -> None:
        with self.repository._connect() as db:
            db.execute(
                "UPDATE production_lots SET status = ? WHERE lot_id = ?",
                (status, lot_id),
            )

    def _series_is_persisted(self, series_id: str) -> bool:
        with self.repository._connect() as db:
            row = db.execute(
                "SELECT COUNT(*) AS card_count FROM cards WHERE series_id = ?",
                (series_id,),
            ).fetchone()
        return int(row["card_count"]) == 6

    def generate_lot(
        self,
        lot_id: int,
        progress_callback: Callable[[int], None] | None = None,
    ) -> ProductionLot:
        lot = self.get_lot(lot_id)
        if lot.status in {"generated", "printed"}:
            raise DuplicateProductionError(f"El lote {lot_id} ya fue generado")

        self._set_status(lot_id, "generating")
        total = lot.card_count
        completed = 0
        for offset in range(0, total, 6):
            first_card = lot.start_card + offset
            series_number = (first_card - 1) // 6 + 1
            series_id = f"{series_number:04d}"

            if self._series_is_persisted(series_id):
                completed += 6
                if progress_callback:
                    progress_callback(completed)
                continue

            try:
                series = self.generator.generate(series_id, lot.model, serial_start=first_card)
                self.repository.save(series)
            except ValueError as exc:
                raise DuplicateProductionError(str(exc)) from exc
            completed += 6
            if progress_callback:
                progress_callback(completed)

        self._set_status(lot_id, "generated")
        return ProductionLot(
            lot_id=lot.lot_id,
            start_card=lot.start_card,
            end_card=lot.end_card,
            series_count=lot.series_count,
            model=lot.model,
            operator=lot.operator,
            status="generated",
            created_at=lot.created_at,
        )

    def mark_printed(self, lot_id: int) -> ProductionLot:
        """Register that a fully generated production lot has been printed."""
        lot = self.get_lot(lot_id)
        if lot.status == "printed":
            raise DuplicateProductionError(f"El lote {lot_id} ya fue marcado como impreso")
        if lot.status != "generated":
            raise ValueError("El lote debe estar generado antes de marcarlo como impreso")
        self._set_status(lot_id, "printed")
        return ProductionLot(
            lot_id=lot.lot_id,
            start_card=lot.start_card,
            end_card=lot.end_card,
            series_count=lot.series_count,
            model=lot.model,
            operator=lot.operator,
            status="printed",
            created_at=lot.created_at,
        )
