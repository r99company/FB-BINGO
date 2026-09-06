from __future__ import annotations

from dataclasses import dataclass
import itertools
import random
from typing import Sequence

from .card import BingoCard, CardModel, COLUMNS, ROWS
from .distribution import CARDS_PER_SERIES, DistributionModel

MAX_SERIAL = 30_000


@dataclass(frozen=True, slots=True)
class BingoSeries:
    """Serie física de seis cartones que cubre una vez los números 1-90."""

    series_id: str
    cards: tuple[BingoCard, ...]

    def __post_init__(self) -> None:
        if not str(self.series_id).strip():
            raise ValueError("El identificador de serie es obligatorio")
        if len(self.cards) != CARDS_PER_SERIES:
            raise ValueError("Una serie debe contener exactamente 6 cartones")
        numbers = [number for card in self.cards for number in card.numbers]
        if len(numbers) != 90 or set(numbers) != set(range(1, 91)):
            raise ValueError("Los 6 cartones de la serie deben cubrir 1-90 exactamente una vez")
        if len({card.serial for card in self.cards}) != CARDS_PER_SERIES:
            raise ValueError("Los seriales de una serie deben ser únicos")


class SeriesGenerator:
    """Genera series de Bingo 90 conservando la matriz exacta de cada cartón.

    El modelo de distribución decide las máscaras/ocupación. Nunca interviene
    en la decisión de línea o bingo.
    """

    def __init__(self, seed: int | None = None, max_serial: int = MAX_SERIAL) -> None:
        if max_serial < CARDS_PER_SERIES:
            raise ValueError("max_serial no permite completar una serie")
        self._rng = random.Random(seed)
        self._max_serial = max_serial

    def generate(
        self,
        series_id: str,
        model: CardModel = CardModel.A,
        serial_start: int = 1,
    ) -> BingoSeries:
        series_id = str(series_id).strip()
        if not series_id:
            raise ValueError("El identificador de serie es obligatorio")
        if serial_start < 1:
            raise ValueError("serial_start debe ser positivo")
        if serial_start + CARDS_PER_SERIES - 1 > self._max_serial:
            raise ValueError(f"Una serie no puede superar el serial {self._max_serial}")

        distribution = DistributionModel.for_model(model)
        for _ in range(1000):
            column_counts = self._column_counts(model, distribution)
            grids = self._build_grids(column_counts, distribution)
            if grids is None:
                continue
            cards = tuple(
                BingoCard(
                    serial=f"{series_id}-{serial_start + index:06d}",
                    model=model,
                    grid=grid,
                )
                for index, grid in enumerate(grids)
            )
            return BingoSeries(series_id=series_id, cards=cards)

        raise RuntimeError("No se pudo generar una serie válida")

    def _column_counts(
        self, model: CardModel, distribution: DistributionModel | None = None
    ) -> list[list[int]]:
        """Build model-specific column loads for a six-card series."""
        distribution = distribution or DistributionModel.for_model(model)
        if model is CardModel.A:
            return distribution.column_counts(self._rng)

        targets = [9] + [10] * 7 + [11]
        max_extra = 2
        remaining = [15 - COLUMNS] * CARDS_PER_SERIES
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        columns = list(range(COLUMNS))
        self._rng.shuffle(columns)
        cache: dict[int, list[tuple[int, ...]]] = {}

        def candidates(extra: int) -> list[tuple[int, ...]]:
            if extra not in cache:
                values = [
                    allocation
                    for allocation in itertools.product(
                        range(max_extra + 1), repeat=CARDS_PER_SERIES
                    )
                    if sum(allocation) == extra
                ]
                self._rng.shuffle(values)
                cache[extra] = values
            return cache[extra]

        def backtrack(position: int, has_three: bool) -> bool:
            if position == COLUMNS:
                return remaining == [0] * CARDS_PER_SERIES and has_three

            column = columns[position]
            extra = targets[column] - CARDS_PER_SERIES
            remaining_columns = COLUMNS - position - 1
            future_extra = sum(
                targets[c] - CARDS_PER_SERIES for c in columns[position + 1 :]
            )
            for allocation in candidates(extra):
                next_remaining = [
                    remaining[i] - allocation[i] for i in range(CARDS_PER_SERIES)
                ]
                if min(next_remaining) < 0:
                    continue
                if sum(next_remaining) != future_extra:
                    continue
                if any(value > remaining_columns * max_extra for value in next_remaining):
                    continue
                old_remaining = remaining[:]
                for card_index, added in enumerate(allocation):
                    result[card_index][column] = 1 + added
                remaining[:] = next_remaining
                if backtrack(position + 1, has_three or 2 in allocation):
                    return True
                remaining[:] = old_remaining
            return False

        if not backtrack(0, False):
            raise RuntimeError("No se pudo equilibrar la distribución de Modelo B")
        return result

    def _balanced_column_counts(self, model: CardModel) -> list[list[int]]:
        """Compatibilidad histórica; delega en las reglas del modelo."""
        return self._column_counts(model)

    def _build_grids(
        self,
        column_counts: Sequence[Sequence[int]],
        distribution: DistributionModel | None = None,
    ) -> list[tuple[tuple[int | None, ...], ...]] | None:
        distribution = distribution or DistributionModel.for_model(CardModel.A)
        row_masks: list[list[int]] = []
        for counts in column_counts:
            masks = distribution.row_masks_for_counts(counts, self._rng)
            if masks is None:
                return None
            row_masks.append(masks)

        grids = [[[None for _ in range(COLUMNS)] for _ in range(ROWS)] for _ in range(CARDS_PER_SERIES)]
        for column in range(COLUMNS):
            values = list(self._values_for_column(column))
            self._rng.shuffle(values)
            cursor = 0
            for card_index in range(CARDS_PER_SERIES):
                count = column_counts[card_index][column]
                card_values = sorted(values[cursor : cursor + count])
                cursor += count
                if len(card_values) != count:
                    return None
                value_index = 0
                mask = row_masks[card_index][column]
                for row in range(ROWS):
                    if mask & (1 << row):
                        grids[card_index][row][column] = card_values[value_index]
                        value_index += 1
            if cursor != len(values):
                return None

        return [tuple(tuple(row) for row in grid) for grid in grids]

    def _row_masks_for_counts(self, counts: Sequence[int]) -> list[int] | None:
        """Compatibilidad histórica; delega al modelo A."""
        return DistributionModel.for_model(CardModel.A).row_masks_for_counts(counts, self._rng)

    @staticmethod
    def _values_for_column(column: int) -> range:
        start = 1 if column == 0 else column * 10
        end = 9 if column == 0 else (column + 1) * 10 - 1
        if column == 8:
            end = 90
        return range(start, end + 1)
