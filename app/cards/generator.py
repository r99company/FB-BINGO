from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence

from .card import BingoCard, CardModel, COLUMNS, ROWS

CARDS_PER_SERIES = 6
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

    El modelo A/B es información de generación e impresión. Nunca interviene
    en la decisión de línea o bingo.
    """

    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

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
        if serial_start + CARDS_PER_SERIES - 1 > MAX_SERIAL:
            raise ValueError(f"Una serie no puede superar el serial {MAX_SERIAL}")

        for _ in range(1000):
            column_counts = self._column_counts(model)
            grids = self._build_grids(column_counts)
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

    def _column_counts(self, model: CardModel) -> list[list[int]]:
        # Totales por columna: 9, 10 x 7 y 11. En conjunto son los 90 números.
        targets = [9] + [10] * 7 + [11]
        extras = [target - CARDS_PER_SERIES for target in targets]
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        loads = [0] * CARDS_PER_SERIES

        for column, extra in enumerate(extras):
            candidates = list(range(CARDS_PER_SERIES))
            self._rng.shuffle(candidates)
            if model is CardModel.A:
                candidates.sort(key=lambda index: (loads[index], index, self._rng.random()))
            else:
                candidates.sort(key=lambda index: (loads[index], -index, self._rng.random()))
            for card_index in candidates[:extra]:
                result[card_index][column] += 1
                loads[card_index] += 1

        if loads != [6] * CARDS_PER_SERIES:
            return self._balanced_column_counts(model)
        return result

    def _balanced_column_counts(self, model: CardModel) -> list[list[int]]:
        targets = [9] + [10] * 7 + [11]
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        loads = [0] * CARDS_PER_SERIES
        for column, target in enumerate(targets):
            extra = target - CARDS_PER_SERIES
            order = list(range(CARDS_PER_SERIES))
            self._rng.shuffle(order)
            if model is CardModel.A:
                order.sort(key=lambda i: (loads[i], i, self._rng.random()))
            else:
                order.sort(key=lambda i: (loads[i], -i, self._rng.random()))
            for card_index in order[:extra]:
                result[card_index][column] += 1
                loads[card_index] += 1
        if loads != [6] * CARDS_PER_SERIES:
            raise RuntimeError("No se pudo equilibrar la distribución de la serie")
        return result

    def _build_grids(
        self, column_counts: Sequence[Sequence[int]]
    ) -> list[tuple[tuple[int | None, ...], ...]] | None:
        row_masks: list[list[int]] = []
        for counts in column_counts:
            masks = self._row_masks_for_counts(counts)
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
        if len(counts) != COLUMNS or sum(counts) != 15:
            return None
        choices = [
            [mask for mask in range(1, 1 << ROWS) if mask.bit_count() == count]
            for count in counts
        ]
        # Randomize the admissible row positions for every column. The previous
        # implementation always selected the first valid mask, which could make
        # several cards look like copies even when their numbers were different.
        for masks in choices:
            self._rng.shuffle(masks)

        chosen = [0] * COLUMNS
        remaining = [5, 5, 5]

        def backtrack(column: int) -> bool:
            if column == COLUMNS:
                return remaining == [0, 0, 0]
            for mask in choices[column]:
                next_remaining = remaining[:]
                for row in range(ROWS):
                    if mask & (1 << row):
                        next_remaining[row] -= 1
                slots_left = COLUMNS - column - 1
                if min(next_remaining) < 0:
                    continue
                if any(value > slots_left * 3 for value in next_remaining):
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
