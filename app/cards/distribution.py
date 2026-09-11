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
        """Genera la ocupación de columnas de una serie de seis.

        Modelo A: las nueve columnas siempre están ocupadas y cada una tiene
        1 o 2 números. Cada cartón tiene exactamente seis columnas dobles y
        tres simples. En la serie, las columnas contienen 9,10,...,10,11
        números respectivamente, permitiendo cubrir 1-90 exactamente una vez.

        Modelo B: conserva la libertad 0-3 por columna.
        """
        if self.model is CardModel.B:
            template = [
                [1, 0, 3, 2, 2, 2, 2, 2, 1],
                [2, 2, 0, 2, 2, 2, 2, 2, 1],
                [2, 2, 1, 0, 2, 2, 1, 2, 3],
                [2, 2, 2, 2, 0, 2, 1, 2, 2],
                [2, 2, 2, 2, 2, 0, 2, 1, 2],
                [0, 2, 2, 2, 2, 2, 2, 1, 2],
            ]
            rng.shuffle(template)
            middle = list(range(1, 8))
            rng.shuffle(middle)
            result = []
            for source in template:
                mapped = [source[0]] + [0] * 7 + [source[8]]
                for target_column, source_column in enumerate(middle, start=1):
                    mapped[target_column] = source[source_column]
                result.append(mapped)
            return result

        target = [3] + [4] * 7 + [5]
        for _ in range(128):
            extras = [[False] * COLUMNS for _ in range(CARDS_PER_SERIES)]
            for card in range(CARDS_PER_SERIES):
                for column in rng.sample(range(COLUMNS), 6):
                    extras[card][column] = True
            totals = [sum(extras[card][column] for card in range(CARDS_PER_SERIES)) for column in range(COLUMNS)]
            guard = 0
            while totals != target and guard < 200:
                guard += 1
                over = [c for c in range(COLUMNS) if totals[c] > target[c]]
                under = [c for c in range(COLUMNS) if totals[c] < target[c]]
                if not over or not under:
                    break
                source = rng.choice(over)
                dest = rng.choice(under)
                candidates = [card for card in range(CARDS_PER_SERIES) if extras[card][source] and not extras[card][dest]]
                if not candidates:
                    break
                card = rng.choice(candidates)
                extras[card][source] = False
                extras[card][dest] = True
                totals[source] -= 1
                totals[dest] += 1
            if totals == target:
                result = [[1 + int(extras[card][column]) for column in range(COLUMNS)] for card in range(CARDS_PER_SERIES)]
                if all(sum(row) == NUMBERS_PER_CARD for row in result):
                    rng.shuffle(result)
                    assert [sum(row[column] for row in result) for column in range(COLUMNS)] == [9] + [10] * 7 + [11]
                    return result
        raise RuntimeError("No se pudo construir una distribución válida del modelo A")

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
        """Puntúa una máscara para favorecer el aspecto alternado de A."""
        score = sum(cls._transitions(mask) for mask in triple) * 18
        score -= sum(max(0, cls._longest_run(mask) - 2) * 35 for mask in triple)
        if len(set(triple)) < 3:
            score -= 240

        column_masks = []
        for column in range(COLUMNS):
            mask = sum((1 << row) for row in range(3) if triple[row] & (1 << column))
            column_masks.append(mask)
        for left, right in zip(column_masks, column_masks[1:]):
            if left == right:
                score -= 110
            else:
                score += 22

        zones = [
            sum(bool(mask & (1 << c)) for mask in triple for c in range(0, 3)),
            sum(bool(mask & (1 << c)) for mask in triple for c in range(3, 6)),
            sum(bool(mask & (1 << c)) for mask in triple for c in range(6, 9)),
        ]
        score -= (max(zones) - min(zones)) * 7
        return score

    def row_masks_for_counts(
        self,
        counts: Sequence[int],
        rng: random.Random,
        forbidden: Sequence[set[int]] | None = None,
    ) -> list[int] | None:
        """Construye tres filas de cinco casillas con posiciones dispersas."""
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None
        max_per_column = 2 if self.model is CardModel.A else 3
        min_per_column = 1 if self.model is CardModel.A else 0
        if any(count < min_per_column or count > max_per_column for count in counts):
            return None
        forbidden = forbidden or [set(), set(), set()]

        # Procesar en orden físico es importante: la regla de alternancia se
        # aplica a columnas vecinas reales, no al orden de dificultad.
        columns = list(range(COLUMNS))
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
            previous_column_mask = None
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
                    if not all(0 <= value <= future for value in nxt) or not possible(position + 1, tuple(nxt)):
                        continue
                    occupied_mask = sum(1 << row for row in range(3) if row not in empty_rows)
                    if self.model is CardModel.A and previous_column_mask == occupied_mask:
                        continue
                    candidates.append((empty_rows, occupied_mask))
                if not candidates:
                    return None
                empty_rows, previous_column_mask = rng.choice(candidates)
                for row in empty_rows:
                    remaining[row] -= 1
                for row in range(3):
                    if row not in empty_rows:
                        masks[row] |= 1 << column
            return tuple(masks)

        best: tuple[int, int, int] | None = None
        best_score = -10**9
        for _ in range(96 if self.model is CardModel.A else 24):
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
