from __future__ import annotations

from collections.abc import Callable
import json

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository

from .models import DEFAULT_PRODUCTION_CAPACITY, ProductionLot, plan_lot


class DuplicateProductionError(RuntimeError):
    """Raised when persisted card data is incomplete or internally inconsistent."""


class ProductionService:
    """Coordinates six-card generation and repeatable printing/reprinting."""

    RECENT_LAYOUT_WINDOW = 60
    MIN_RECENT_LAYOUT_DISTANCE = 6
    RELAXED_LAYOUT_DISTANCES = (6, 4, 2, 0)
    MAX_LAYOUT_RETRIES = 12

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

    def _existing_serials_for_range(self, start_card: int, end_card: int) -> list[str]:
        with self.repository._connect() as db:
            rows = db.execute(
                """
                SELECT serial FROM cards
                WHERE CAST(substr(serial, -6) AS INTEGER) BETWEEN ? AND ?
                ORDER BY CAST(substr(serial, -6) AS INTEGER)
                """,
                (start_card, end_card),
            ).fetchall()
        return [str(row["serial"]) for row in rows]

    @staticmethod
    def _expected_serials(start_card: int, end_card: int, series_id: str | None = None) -> list[str]:
        if series_id is None:
            return [f"{((number - 1) // 6 + 1):04d}-{number:06d}" for number in range(start_card, end_card + 1)]
        return [f"{series_id}-{number:06d}" for number in range(start_card, end_card + 1)]

    def _range_is_fully_persisted(self, start_card: int, end_card: int) -> bool:
        persisted = self._existing_serials_for_range(start_card, end_card)
        return bool(persisted) and persisted == self._expected_serials(start_card, end_card)

    @staticmethod
    def _canonical_series_ranges(start_card: int, end_card: int):
        first_series = (start_card - 1) // 6 + 1
        last_series = (end_card - 1) // 6 + 1
        for series_number in range(first_series, last_series + 1):
            canonical_start = (series_number - 1) * 6 + 1
            canonical_end = canonical_start + 5
            yield f"{series_number:04d}", canonical_start, canonical_end

    @staticmethod
    def _layout_signature(card) -> str:
        return json.dumps(card.grid, separators=(",", ":"), ensure_ascii=False)

    @staticmethod
    def _layout_mask(card) -> tuple[tuple[bool, ...], ...]:
        return tuple(tuple(cell is not None for cell in row) for row in card.grid)

    @staticmethod
    def _mask_distance(first, second) -> int:
        return sum(left != right for row_left, row_right in zip(first, second) for left, right in zip(row_left, row_right))

    def _candidate_is_unique_and_dynamic(self, series, used_layouts: set[str], recent_masks: list, min_distance: int) -> bool:
        signatures = [self._layout_signature(card) for card in series.cards]
        if len(signatures) != len(set(signatures)):
            return False
        if any(signature in used_layouts for signature in signatures):
            return False

        masks = [self._layout_mask(card) for card in series.cards]
        for left in range(len(masks)):
            for right in range(left + 1, len(masks)):
                if self._mask_distance(masks[left], masks[right]) < min_distance:
                    return False

        if min_distance:
            for mask in masks:
                if any(self._mask_distance(mask, previous) < min_distance for previous in recent_masks):
                    return False
        return True

    def create_lot(self, start_card: int, end_card: int, model: CardModel = CardModel.A, operator: str = "") -> ProductionLot:
        planned = plan_lot(start_card, end_card, model=model, operator=operator, max_cards=self.max_cards)
        with self.repository._connect() as db:
            row = db.execute("SELECT COALESCE(MAX(lot_id), 0) + 1 AS next_id FROM production_lots").fetchone()
            lot = ProductionLot(
                lot_id=int(row["next_id"]), start_card=planned.start_card, end_card=planned.end_card,
                series_count=planned.series_count, model=planned.model, operator=planned.operator,
                status=planned.status, created_at=planned.created_at,
            )
            db.execute(
                "INSERT INTO production_lots(lot_id,start_card,end_card,series_count,model,operator,status,created_at) VALUES (?,?,?,?,?,?,?,?)",
                (lot.lot_id, lot.start_card, lot.end_card, lot.series_count, lot.model.value, lot.operator, lot.status, lot.created_at),
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
            db.execute("UPDATE production_lots SET status = ? WHERE lot_id = ?", (status, lot_id))

    def _series_is_persisted(self, series_id: str, expected_start: int) -> bool:
        expected = self._expected_serials(expected_start, expected_start + 5, series_id)
        with self.repository._connect() as db:
            rows = db.execute("SELECT serial FROM cards WHERE series_id = ? ORDER BY card_index", (series_id,)).fetchall()
        persisted = [str(row["serial"]) for row in rows]
        if not persisted:
            return False
        if persisted != expected:
            raise DuplicateProductionError(
                f"La serie {series_id} ya existe pero sus cartones no corresponden al rango {expected_start}-{expected_start + 5}"
            )
        return True

    def generate_lot(self, lot_id: int, progress_callback: Callable[[int], None] | None = None) -> ProductionLot:
        lot = self.get_lot(lot_id)

        # Un lote marcado como generado/impreso solo se puede reutilizar sin
        # regenerar cuando TODOS sus cartones realmente existen en la BD.
        # Esto permite recuperar lotes que quedaron marcados por una ejecución
        # anterior que falló antes de persistir las matrices.
        if lot.status in {"generated", "printed"} and self._range_is_fully_persisted(lot.start_card, lot.end_card):
            result = ProductionLot(
                lot_id=lot.lot_id, start_card=lot.start_card, end_card=lot.end_card,
                series_count=lot.series_count, model=lot.model, operator=lot.operator,
                status=lot.status, created_at=lot.created_at,
            )
            if progress_callback:
                progress_callback(lot.card_count)
            return result

        self._set_status(lot_id, "generating")
        completed = 0
        used_layouts = self.repository.get_grid_signatures()
        recent_masks = [self._layout_mask(card) for card in self.repository.get_recent_cards(self.RECENT_LAYOUT_WINDOW)]

        try:
            for series_id, canonical_start, canonical_end in self._canonical_series_ranges(lot.start_card, lot.end_card):
                if canonical_end > self.max_cards:
                    raise ValueError(f"La serie {series_id} supera la capacidad de {self.max_cards:,} cartones")

                if not self._series_is_persisted(series_id, canonical_start):
                    series = None
                    for min_distance in self.RELAXED_LAYOUT_DISTANCES:
                        for _ in range(self.MAX_LAYOUT_RETRIES):
                            candidate = self.generator.generate(series_id, lot.model, serial_start=canonical_start)
                            if self._candidate_is_unique_and_dynamic(candidate, used_layouts, recent_masks, min_distance):
                                series = candidate
                                break
                        if series is not None:
                            break

                    if series is None:
                        raise DuplicateProductionError(
                            f"No se pudo encontrar una distribución nueva para la serie {series_id}. "
                            "La biblioteca actual puede contener demasiados patrones similares."
                        )
                    try:
                        self.repository.save(series)
                    except ValueError as exc:
                        raise DuplicateProductionError(str(exc)) from exc

                    masks = [self._layout_mask(card) for card in series.cards]
                    used_layouts.update(self._layout_signature(card) for card in series.cards)
                    recent_masks.extend(masks)
                    if len(recent_masks) > self.RECENT_LAYOUT_WINDOW:
                        recent_masks[:] = recent_masks[-self.RECENT_LAYOUT_WINDOW:]

                overlap_start = max(lot.start_card, canonical_start)
                overlap_end = min(lot.end_card, canonical_end)
                completed += max(0, overlap_end - overlap_start + 1)
                if progress_callback:
                    progress_callback(completed)
        except Exception:
            self._set_status(lot_id, "failed")
            raise

        self._set_status(lot_id, "generated")
        return ProductionLot(
            lot_id=lot.lot_id, start_card=lot.start_card, end_card=lot.end_card,
            series_count=lot.series_count, model=lot.model, operator=lot.operator,
            status="generated", created_at=lot.created_at,
        )

    def mark_printed(self, lot_id: int) -> ProductionLot:
        lot = self.get_lot(lot_id)
        if lot.status == "printed":
            return lot
        if lot.status != "generated":
            raise ValueError("El lote debe estar generado antes de marcarlo como impreso")
        self._set_status(lot_id, "printed")
        return ProductionLot(
            lot_id=lot.lot_id, start_card=lot.start_card, end_card=lot.end_card,
            series_count=lot.series_count, model=lot.model, operator=lot.operator,
            status="printed", created_at=lot.created_at,
        )
