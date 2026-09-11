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
        """Devuelve una plantilla válida de ocupación para una serie de 6.

        No se fuerza un número en las nueve columnas. Cada cartón tiene 15
        números y al menos una columna vacía; A usa 0–2 y B 0–3. Las columnas
        de la serie suman 9, 10, ..., 10, 11, por lo que entre los seis
        cartones aparecen una vez todos los números 1–90.
        """
        if self.model is CardModel.A:
            template = [
                [1, 0, 2, 2, 2, 2, 2, 2, 2],
                [2, 2, 0, 2, 2, 2, 2, 2, 1],
                [2, 2, 2, 0, 2, 2, 1, 2, 2],
                [2, 2, 2, 2, 0, 2, 1, 2, 2],
                [2, 2, 2, 2, 2, 0, 2, 1, 2],
                [0, 2, 2, 2, 2, 2, 2, 1, 2],
            ]
        else:
            template = [
                [1, 0, 3, 2, 2, 2, 2, 2, 1],
                [2, 2, 0, 2, 2, 2, 2, 2, 1],
                [2, 2, 1, 0, 2, 2, 1, 2, 3],
                [2, 2, 2, 2, 0, 2, 1, 2, 2],
                [2, 2, 2, 2, 2, 0, 2, 1, 2],
                [0, 2, 2, 2, 2, 2, 2, 1, 2],
            ]
        middle = list(range(1, 8))
        rng.shuffle(middle)
        card_order = list(range(CARDS_PER_SERIES))
        rng.shuffle(card_order)
        result = []
        for source in card_order:
            row = template[source]
            mapped = [row[0]] + [0] * 7 + [row[8]]
            for target_column, source_column in enumerate(middle, start=1):
                mapped[target_column] = row[source_column]
            result.append(mapped)
        assert [sum(row[column] for row in result) for column in range(COLUMNS)] == [9] + [10] * 7 + [11]
        assert all(sum(row) == NUMBERS_PER_CARD and 0 in row for row in result)
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
