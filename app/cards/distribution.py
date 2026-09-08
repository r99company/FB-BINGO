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

        # Model A is the compact/interleaved format used by FB-BINGO: avoid
        # visually monotonous runs longer than three occupied cells in a row.
        # Model B keeps the more permissive legacy layout because it can place
        # three numbers in a column.
        max_consecutive = 3 if self.model is CardModel.A else 4
        column_order = sorted(range(COLUMNS), key=lambda c: (counts[c], rng.random()))
        chosen = [0] * COLUMNS
        remaining = [5, 5, 5]

        def respects_spacing(column: int, mask: int) -> bool:
            chosen[column] = mask
            for row in range(ROWS):
                run = 0
                for current_column in range(COLUMNS):
                    if chosen[current_column] & (1 << row):
                        run += 1
                        if run > max_consecutive:
                            chosen[column] = 0
                            return False
                    else:
                        run = 0
            chosen[column] = 0
            return True

        def backtrack(position: int) -> bool:
            if position == COLUMNS:
                return remaining == [0, 0, 0]

            column = column_order[position]
            slots_left = COLUMNS - position - 1
            for mask in choices[column]:
                next_remaining = remaining[:]
                for row in range(ROWS):
                    if mask & (1 << row):
                        next_remaining[row] -= 1
                if min(next_remaining) < 0:
                    continue
                if any(value > slots_left * 3 for value in next_remaining):
                    continue
                if not respects_spacing(column, mask):
                    continue

                chosen[column] = mask
                old = remaining[:]
                remaining[:] = next_remaining
                if backtrack(position + 1):
                    return True
                remaining[:] = old
                chosen[column] = 0
            return False

        return chosen if backtrack(0) else None
