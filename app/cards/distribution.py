from __future__ import annotations

from dataclasses import dataclass
import itertools
import random
from functools import lru_cache
from typing import Sequence

from .card import COLUMNS, CardModel

CARDS_PER_SERIES = 6
NUMBERS_PER_CARD = 15


@dataclass(frozen=True, slots=True)
class DistributionModel:
    """Reglas de ocupación de casillas para Bingo de 90 bolas."""

    model: CardModel

    @classmethod
    def for_model(cls, model: CardModel) -> "DistributionModel":
        if not isinstance(model, CardModel):
            raise ValueError("El modelo de distribución no es válido")
        return cls(model=model)

    def column_counts(self, rng: random.Random) -> list[list[int]]:
        """Distribuye 90 números entre 6 cartones sin forzar las 9 columnas."""
        targets = [9] + [10] * 7 + [11]
        max_per_column = 2 if self.model is CardModel.A else 3
        full_mask = (1 << CARDS_PER_SERIES) - 1
        columns = sorted(range(COLUMNS), key=lambda c: (-targets[c], rng.random()))
        cache: dict[tuple[int, int], list[tuple[int, ...]]] = {}

        def candidates(total: int) -> list[tuple[int, ...]]:
            key = (total, max_per_column)
            if key not in cache:
                values = [
                    allocation
                    for allocation in itertools.product(range(max_per_column + 1), repeat=CARDS_PER_SERIES)
                    if sum(allocation) == total
                ]
                rng.shuffle(values)
                cache[key] = values
            return cache[key]

        for _attempt in range(64):
            remaining = [NUMBERS_PER_CARD] * CARDS_PER_SERIES
            result = [[0] * COLUMNS for _ in range(CARDS_PER_SERIES)]

            def assign(position: int, zero_mask: int) -> bool:
                if position == COLUMNS:
                    return remaining == [0] * CARDS_PER_SERIES and zero_mask == full_mask
                column = columns[position]
                future_columns = columns[position + 1:]
                future_count = len(future_columns)
                future_total = sum(targets[c] for c in future_columns)
                for allocation in candidates(targets[column]):
                    next_remaining = [remaining[i] - allocation[i] for i in range(CARDS_PER_SERIES)]
                    if min(next_remaining) < 0 or sum(next_remaining) != future_total:
                        continue
                    if any(value > future_count * max_per_column for value in next_remaining):
                        continue
                    next_zero_mask = zero_mask
                    for card_index, count in enumerate(allocation):
                        if count == 0:
                            next_zero_mask |= 1 << card_index
                    if future_count == 0 and next_zero_mask != full_mask:
                        continue
                    if future_count:
                        impossible_zero = any(
                            not (next_zero_mask & (1 << i))
                            and next_remaining[i] == future_count * max_per_column
                            for i in range(CARDS_PER_SERIES)
                        )
                        if impossible_zero:
                            continue
                    old_remaining = remaining[:]
                    for card_index, count in enumerate(allocation):
                        result[card_index][column] = count
                    remaining[:] = next_remaining
                    if assign(position + 1, next_zero_mask):
                        return True
                    remaining[:] = old_remaining
                return False

            if assign(0, 0):
                return result

        raise RuntimeError(f"No se pudo equilibrar la distribución del Modelo {self.model.value}")

    @staticmethod
    def _transitions(mask: int) -> int:
        previous = False
        transitions = 0
        for column in range(COLUMNS):
            occupied = bool(mask & (1 << column))
            if column and occupied != previous:
                transitions += 1
            previous = occupied
        return transitions

    @staticmethod
    def _longest_run(mask: int) -> int:
        run = longest = 0
        for column in range(COLUMNS):
            if mask & (1 << column):
                run += 1
                longest = max(longest, run)
            else:
                run = 0
        return longest

    @classmethod
    def _triple_score(cls, triple: tuple[int, int, int]) -> int:
        score = sum(cls._transitions(mask) for mask in triple) * 8
        score -= sum(max(0, cls._longest_run(mask) - 2) * 18 for mask in triple)
        if len(set(triple)) < 3:
            score -= 120
        prefix = [sum(bool(mask & (1 << c)) for c in range(4)) for mask in triple]
        suffix = [sum(bool(mask & (1 << c)) for c in range(5, 9)) for mask in triple]
        score -= (max(prefix) - min(prefix)) * 3
        score -= (max(suffix) - min(suffix)) * 3
        center = [sum(bool(mask & (1 << c)) for c in range(2, 7)) for mask in triple]
        score -= sum(abs(value - 3) for value in center)
        return score

    def row_masks_for_counts(
        self,
        counts: Sequence[int],
        rng: random.Random,
        forbidden: Sequence[set[int]] | None = None,
    ) -> list[int] | None:
        """Construye tres filas de cinco casillas con separación visual variable."""
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None
        max_per_column = 2 if self.model is CardModel.A else 3
        if any(count < 0 or count > max_per_column for count in counts):
            return None
        forbidden = forbidden or [set(), set(), set()]

        columns = sorted(range(COLUMNS), key=lambda c: (-counts[c], rng.random()))
        empty_counts = tuple(3 - count for count in counts)
        choices = {
            empty_count: list(itertools.combinations(range(3), empty_count))
            for empty_count in range(4)
        }
        for values in choices.values():
            rng.shuffle(values)

        @lru_cache(maxsize=None)
        def possible(position: int, remaining: tuple[int, int, int]) -> bool:
            if position == COLUMNS:
                return remaining == (0, 0, 0)
            column = columns[position]
            future = COLUMNS - position - 1
            empty_count = empty_counts[column]
            for empty_rows in choices[empty_count]:
                if any(remaining[row] <= 0 for row in empty_rows):
                    continue
                nxt = list(remaining)
                for row in empty_rows:
                    nxt[row] -= 1
                if all(0 <= value <= future for value in nxt) and possible(position + 1, tuple(nxt)):
                    return True
            return False

        if not possible(0, (4, 4, 4)):
            return None

        def build_once() -> tuple[int, int, int] | None:
            remaining = [4, 4, 4]
            masks = [0, 0, 0]
            for position, column in enumerate(columns):
                future = COLUMNS - position - 1
                empty_count = empty_counts[column]
                candidates = []
                for empty_rows in choices[empty_count]:
                    if any(remaining[row] <= 0 for row in empty_rows):
                        continue
                    nxt = list(remaining)
                    for row in empty_rows:
                        nxt[row] -= 1
                    if all(0 <= value <= future for value in nxt) and possible(position + 1, tuple(nxt)):
                        candidates.append(empty_rows)
                if not candidates:
                    return None
                empty_rows = rng.choice(candidates)
                for row in empty_rows:
                    remaining[row] -= 1
                for row in range(3):
                    if row not in empty_rows:
                        masks[row] |= 1 << column
            return tuple(masks)

        best: tuple[int, int, int] | None = None
        best_score = -10**9
        for _ in range(24):
            candidate = build_once()
            if candidate is None:
                continue
            if any(candidate[row] in forbidden[row] for row in range(3)):
                continue
            score = self._triple_score(candidate)
            if score > best_score:
                best_score = score
                best = candidate
        return list(best) if best is not None else None
