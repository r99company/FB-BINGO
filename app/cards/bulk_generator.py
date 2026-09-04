from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from .card import CardModel
from .generator import CARDS_PER_SERIES, MAX_SERIAL, BingoSeries, SeriesGenerator
from app.database import SQLiteSeriesRepository

TOTAL_SERIES = 2_500
TOTAL_CARDS = TOTAL_SERIES * CARDS_PER_SERIES
BATCH_SIZE = 100


@dataclass(frozen=True, slots=True)
class BulkGenerationResult:
    series_generated: int
    cards_generated: int
    first_series: int
    last_series: int
    first_serial: int
    last_serial: int


class BulkSeriesGenerator:
    """Genera y persiste lotes grandes de series con transacciones agrupadas."""

    def __init__(self, repository: SQLiteSeriesRepository, seed: int | None = None) -> None:
        self.repository = repository
        self.generator = SeriesGenerator(seed=seed)

    def generate(
        self,
        start_series: int = 1,
        quantity: int = TOTAL_SERIES,
        model: CardModel = CardModel.A,
        serial_start: int = 1,
        progress: Callable[[int, int], None] | None = None,
    ) -> BulkGenerationResult:
        if quantity < 1 or start_series < 1 or serial_start < 1:
            raise ValueError("Los valores iniciales y la cantidad deben ser positivos")
        last_series = start_series + quantity - 1
        last_serial = serial_start + quantity * CARDS_PER_SERIES - 1
        if last_serial > MAX_SERIAL:
            raise ValueError(f"El lote supera el serial máximo {MAX_SERIAL}")

        batch: list[BingoSeries] = []
        for offset in range(quantity):
            series_number = start_series + offset
            batch.append(
                self.generator.generate(
                    series_id=str(series_number),
                    model=model,
                    serial_start=serial_start + offset * CARDS_PER_SERIES,
                )
            )
            if len(batch) >= BATCH_SIZE or offset == quantity - 1:
                self.repository.save_many(batch)
                if progress is not None:
                    progress(offset + 1, quantity)
                batch.clear()

        return BulkGenerationResult(
            series_generated=quantity,
            cards_generated=quantity * CARDS_PER_SERIES,
            first_series=start_series,
            last_series=last_series,
            first_serial=serial_start,
            last_serial=last_serial,
        )
