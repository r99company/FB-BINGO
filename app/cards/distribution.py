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

        # Keep the physical column order while solving the mask. This makes
        # adjacency constraints meaningful for the final printed card.
        max_consecutive = 3 if self.model is CardModel.A else 4
        column_order = list(range(COLUMNS))
        chosen = [0] * COLUMNS
        remaining = [5, 5, 5]

        def prefix_counts() -> list[int]:
            return [
                sum(bool(chosen[column] & (1 << row)) for column in range(4))
                for row in range(ROWS)
            ]

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

        def visual_score(column: int, mask: int) -> tuple[int, int, float]:
            """Prefer alternating rows without making the layout deterministic."""
            score = 0
            if column > 0:
                score += 4 * sum(
                    bool(mask & (1 << row)) and bool(chosen[column - 1] & (1 << row))
                    for row in range(ROWS)
                )
            if column < 4:
                counts_now = [
                    sum(
                        bool(chosen[c] & (1 << row))
                        for c in range(column + 1)
                    )
                    + (1 if mask & (1 << row) else 0)
                    for row in range(ROWS)
                ]
                score += 6 * (max(counts_now) - min(counts_now))
            return (score, sum(bool(mask & (1 << row)) for row in range(ROWS)), rng.random())

        def backtrack(position: int) -> bool:
            if position == COLUMNS:
                return remaining == [0, 0, 0]

            column = column_order[position]
            slots_left = COLUMNS - position - 1
            candidates = []
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
                if column == 3:
                    first_four = prefix_counts()
                    if max(first_four) - min(first_four) > 1 or min(first_four) == 0:
                        chosen[column] = 0
                        continue
                chosen[column] = 0
                candidates.append(mask)

            candidates.sort(key=lambda mask: visual_score(column, mask))
            for mask in candidates:
                chosen[column] = mask
                next_remaining = remaining[:]
                for row in range(ROWS):
                    if mask & (1 << row):
                        next_remaining[row] -= 1
                old = remaining[:]
                remaining[:] = next_remaining
                if backtrack(position + 1):
                    return True
                remaining[:] = old
                chosen[column] = 0
            return False

        return chosen if backtrack(0) else None
