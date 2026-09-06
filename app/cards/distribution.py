from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence

from .card import COLUMNS, ROWS, CardModel

CARDS_PER_SERIES = 6
NUMBERS_PER_CARD = 15


@dataclass(frozen=True, slots=True)
class DistributionModel:
    """Define how a card model distributes occupied cells within a series.

    The Bingo rules remain outside this object. The model only decides column
    loads and row masks; number selection and card validation stay in the core.
    """

    model: CardModel

    @classmethod
    def for_model(cls, model: CardModel) -> "DistributionModel":
        if not isinstance(model, CardModel):
            raise ValueError("El modelo de distribución no es válido")
        return cls(model=model)

    def column_counts(self, rng: random.Random) -> list[list[int]]:
        targets = [9] + [10] * 7 + [11]
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        loads = [0] * CARDS_PER_SERIES

        for column, target in enumerate(targets):
            extra = target - CARDS_PER_SERIES
            order = list(range(CARDS_PER_SERIES))
            rng.shuffle(order)
            if self.model is CardModel.A:
                order.sort(key=lambda i: (loads[i], i, rng.random()))
            else:
                order.sort(key=lambda i: (loads[i], -i, rng.random()))
            for card_index in order[:extra]:
                result[card_index][column] += 1
                loads[card_index] += 1

        if loads != [6] * CARDS_PER_SERIES:
            raise RuntimeError("No se pudo equilibrar la distribución de la serie")
        return result

    def row_masks_for_counts(
        self, counts: Sequence[int], rng: random.Random
    ) -> list[int] | None:
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None

        choices = [
            [mask for mask in range(1, 1 << ROWS) if mask.bit_count() == count]
            for count in counts
        ]
        for masks in choices:
            rng.shuffle(masks)

        chosen = [0] * COLUMNS
        remaining = [5, 5, 5]

        def backtrack(column: int) -> bool:
            if column == COLUMNS:
                return remaining == [0, 0, 0]

            slots_left = COLUMNS - column - 1
            for mask in choices[column]:
                next_remaining = remaining[:]
                for row in range(ROWS):
                    if mask & (1 << row):
                        next_remaining[row] -= 1
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
