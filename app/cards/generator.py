from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence

from .card import BingoCard, CardModel, COLUMNS, ROWS

CARDS_PER_SERIES = 6


@dataclass(frozen=True, slots=True)
class BingoSeries:
    """Serie física de seis cartones que cubre una vez los números 1-90."""

    series_id: str
    cards: tuple[BingoCard, ...]

    def __post_init__(self) -> None:
        if not self.series_id.strip():
            raise ValueError("El identificador de serie es obligatorio")
        if len(self.cards) != CARDS_PER_SERIES:
            raise ValueError("Una serie debe contener exactamente 6 cartones")
        numbers = [number for card in self.cards for number in card.numbers]
        if len(numbers) != 90 or set(numbers) != set(range(1, 91)):
            raise ValueError("Los 6 cartones de la serie deben cubrir 1-90 exactamente una vez")
        if len({card.serial for card in self.cards}) != CARDS_PER_SERIES:
            raise ValueError("Los seriales de una serie deben ser únicos")


class SeriesGenerator:
    """Genera series estándar de Bingo 90 manteniendo la matriz exacta de cada cartón.

    El modelo A/B es metadata de generación/impresión. Nunca se usa para decidir premios.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def generate(
        self,
        series_id: str,
        model: CardModel = CardModel.A,
        serial_start: int = 1,
    ) -> BingoSeries:
        if serial_start < 1:
            raise ValueError("serial_start debe ser positivo")

        for _ in range(1000):
            column_counts = self._column_counts(model)
            grids = self._build_grids(column_counts)
            if grids is None:
                continue
            cards: list[BingoCard] = []
            for index, grid in enumerate(grids):
                cards.append(
                    BingoCard(
                        serial=f"{series_id}-{serial_start + index:06d}",
                        model=model,
                        grid=grid,
                    )
                )
            return BingoSeries(series_id=series_id, cards=tuple(cards))

        raise RuntimeError("No se pudo generar una serie válida después de varios intentos")

    def _column_counts(self, model: CardModel) -> list[list[int]]:
        # En una serie estándar, cada columna cubre todos sus números una sola vez.
        targets = [9] + [10] * 7 + [11]
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        for column, target in enumerate(targets):
            extra = target - CARDS_PER_SERIES
            order = list(range(CARDS_PER_SERIES))
            self._rng.shuffle(order)
            # A favorece columnas de 2/3; B favorece una distribución más ligera.
            if model is CardModel.A:
                for card_index in order[:extra]:
                    result[card_index][column] += 1
            else:
                order.reverse()
                for card_index in order[:extra]:
                    result[card_index][column] += 1
        return result

    def _build_grids(self, column_counts: Sequence[Sequence[int]]) -> list[tuple[tuple[int | None, ...], ...]] | None:
        grids: list[tuple[tuple[int | None, ...], ...]] = []
        for counts in column_counts:
            masks = self._row_masks_for_counts(counts)
            if masks is None:
                return None
            grid = [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
            column_values = [list(self._values_for_column(column)) for column in range(COLUMNS)]
            for column in range(COLUMNS):
                self._rng.shuffle(column_values[column])
                values = sorted(column_values[column][: counts[column]])
                rows = [row for row in range(ROWS) if masks[column] & (1 << row)]
                for row, value in zip(rows, values):
                    grid[row][column] = value
            grids.append(tuple(tuple(row) for row in grid))

        # Los números deben aparecer una sola vez en la serie.
        # Reasignamos valores por columna a las seis tarjetas según sus cantidades.
        mutable = [
            [[None for _ in range(COLUMNS)] for _ in range(ROWS)]
            for _ in range(CARDS_PER_SERIES)
        ]
        for column in range(COLUMNS):
            values = list(self._values_for_column(column))
            self._rng.shuffle(values)
            cursor = 0
            for card_index in range(CARDS_PER_SERIES):
                count = column_counts[card_index][column]
                rows = [row for row in range(ROWS) if self._row_mask_cache(column_counts[card_index], column, grids[card_index]) & (1 << row)]
                for row in rows:
                    mutable[card_index][row][column] = values[cursor]
                    cursor += 1

        return [tuple(tuple(row) for row in grid) for grid in mutable]

    @staticmethod
    def _row_mask_cache(counts: Sequence[int], column: int, grid: tuple[tuple[int | None, ...], ...]) -> int:
        return sum((1 << row) for row in range(ROWS) if grid[row][column] is not None)

    def _row_masks_for_counts(self, counts: Sequence[int]) -> list[int] | None:
        if sum(counts) != 15 or len(counts) != COLUMNS:
            return None
        masks_by_column: list[list[int]] = []
        for count in counts:
            masks_by_column.append([mask for mask in range(1, 1 << ROWS) if mask.bit_count() == count])

        chosen = [0] * COLUMNS
        remaining = [5, 5, 5]

        def backtrack(column: int) -> bool:
            if column == COLUMNS:
                return remaining == [0, 0, 0]
            count = counts[column]
            for mask in masks_by_column[column]:
                next_remaining = remaining[:]
                for row in range(ROWS):
                    if mask & (1 << row):
                        next_remaining[row] -= 1
                if min(next_remaining) < 0:
                    continue
                slots_left = COLUMNS - column - 1
                if any(value > slots_left * 3 for value in next_remaining):
                    continue
                if any(value < 0 for value in next_remaining):
                    continue
                chosen[column] = mask
                old = remaining[:]
                remaining[:] = next_remaining
                if backtrack(column + 1):
                    return True
                remaining[:] = old
            return False

        return chosen if backtrack(0) else None

    @staticmethod
    def _values_for_column(column: int) -> range:
        start = 1 if column == 0 else column * 10
        end = 9 if column == 0 else (column + 1) * 10 - 1
        if column == 8:
            end = 90
        return range(start, end + 1)
