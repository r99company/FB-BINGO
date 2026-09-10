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
        targets = [9] + [10] * 7 + [11]
        extras = [target - CARDS_PER_SERIES for target in targets]
        remaining = [6] * CARDS_PER_SERIES
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        columns = sorted(range(COLUMNS), key=lambda c: (-extras[c], rng.random()))

        def assign(position: int) -> bool:
            if position == COLUMNS:
                return remaining == [0] * CARDS_PER_SERIES
            column = columns[position]
            need = extras[column]
            future = COLUMNS - position - 1
            choices = list(itertools.combinations(range(CARDS_PER_SERIES), need))
            rng.shuffle(choices)
            for selected in choices:
                if any(remaining[i] <= 0 for i in selected):
                    continue
                for i in selected:
                    remaining[i] -= 1
                    result[i][column] += 1
                if all(value <= future for value in remaining) and assign(position + 1):
                    return True
                for i in selected:
                    remaining[i] += 1
                    result[i][column] -= 1
            return False

        if not assign(0):
            raise RuntimeError("No se pudo equilibrar la distribución de la serie")
        return result

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

    @classmethod
    def _triple_score(cls, triple: tuple[int, int, int]) -> int:
        score = sum(cls._transitions(mask) for mask in triple) * 5
        prefix = [sum(bool(mask & (1 << c)) for c in range(4)) for mask in triple]
        suffix = [sum(bool(mask & (1 << c)) for c in range(5, 9)) for mask in triple]
        score -= (max(prefix) - min(prefix)) * 3
        score -= (max(suffix) - min(suffix)) * 3
        center = [sum(bool(mask & (1 << c)) for c in range(2, 7)) for mask in triple]
        score -= sum(abs(value - 3) for value in center)
        return score

    def row_masks_for_counts(self, counts: Sequence[int], rng: random.Random, forbidden: Sequence[set[int]] | None = None) -> list[int] | None:
        """Construye tres máscaras de cinco casillas de forma determinista y rápida."""
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None
        max_per_column = 2 if self.model is CardModel.A else 3
        if any(count < 1 or count > max_per_column for count in counts):
            return None
        forbidden = forbidden or [set(), set(), set()]
        columns = sorted(range(COLUMNS), key=lambda c: (-counts[c], rng.random()))
        choices = {n: list(itertools.combinations(range(3), n)) for n in range(1, max_per_column + 1)}
        for values in choices.values():
            rng.shuffle(values)

        @lru_cache(maxsize=None)
        def possible(position: int, remaining: tuple[int, int, int]) -> bool:
            if position == COLUMNS:
                return remaining == (0, 0, 0)
            column = columns[position]
            future = COLUMNS - position - 1
            for rows in choices[counts[column]]:
                if any(remaining[row] <= 0 for row in rows):
                    continue
                nxt = list(remaining)
                for row in rows:
                    nxt[row] -= 1
                if all(0 <= value <= future for value in nxt) and possible(position + 1, tuple(nxt)):
                    return True
            return False

        if not possible(0, (5, 5, 5)):
            return None

        def build(prefer_forbidden: bool = False) -> tuple[int, int, int] | None:
            remaining = [5, 5, 5]
            masks = [0, 0, 0]
            for position, column in enumerate(columns):
                future = COLUMNS - position - 1
                candidates = []
                for rows in choices[counts[column]]:
                    if any(remaining[row] <= 0 for row in rows):
                        continue
                    nxt = list(remaining)
                    for row in rows:
                        nxt[row] -= 1
                    if all(0 <= value <= future for value in nxt) and possible(position + 1, tuple(nxt)):
                        candidates.append(rows)
                if not candidates:
                    return None
                if prefer_forbidden:
                    rng.shuffle(candidates)
                rows = rng.choice(candidates)
                for row in rows:
                    remaining[row] -= 1
                    masks[row] |= 1 << column
            return tuple(masks)

        for attempt in range(16):
            triple = build(prefer_forbidden=attempt > 0)
            if triple is not None and not any(triple[row] in forbidden[row] for row in range(3)):
                return list(triple)
        return None
