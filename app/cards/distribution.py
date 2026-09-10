from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence

from .card import COLUMNS, CardModel

CARDS_PER_SERIES = 6
NUMBERS_PER_CARD = 15


@dataclass(frozen=True, slots=True)
class DistributionModel:
    """Define how a card model distributes occupied cells within a series."""

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

    @staticmethod
    def _row_patterns(max_run: int) -> list[int]:
        patterns: list[tuple[int, int]] = []
        for mask in range(1, 1 << COLUMNS):
            if mask.bit_count() != 5:
                continue

            longest = current = 0
            transitions = 0
            previous = False
            for column in range(COLUMNS):
                occupied = bool(mask & (1 << column))
                if occupied:
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 0
                if column and occupied != previous:
                    transitions += 1
                previous = occupied

            # Las series de referencia tienen una lectura visual aireada:
            # nunca aparecen 3 o 4 casillas ocupadas seguidas.
            if longest > max_run:
                continue

            # La primera y la última zona no deben quedar sobrecargadas.
            # Esto evita el efecto de "cuatro números pegados" y hace que
            # el patrón tenga movimiento desde el centro hacia los extremos.
            prefix = sum(bool(mask & (1 << column)) for column in range(4))
            suffix = sum(bool(mask & (1 << column)) for column in range(5, 9))
            if not 1 <= prefix <= 2:
                continue
            if not 1 <= suffix <= 2:
                continue

            # Más transiciones = más espacios intercalados y menos aspecto
            # de "bloque". Las máscaras con la misma puntuación se mezclan
            # después usando el generador aleatorio de la serie.
            patterns.append((transitions, mask))

        patterns.sort(key=lambda item: item[0], reverse=True)
        return [mask for _, mask in patterns]

    @staticmethod
    def _pattern_transitions(mask: int) -> int:
        transitions = 0
        previous = False
        for column in range(COLUMNS):
            occupied = bool(mask & (1 << column))
            if column and occupied != previous:
                transitions += 1
            previous = occupied
        return transitions

    def row_masks_for_counts(
        self, counts: Sequence[int], rng: random.Random
    ) -> list[int] | None:
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None
        if any(count < 1 or count > (2 if self.model is CardModel.A else 3) for count in counts):
            return None

        # Ambos modelos conservan el aspecto visual de las series de referencia:
        # puede haber pares consecutivos, pero nunca bloques largos de 3+.
        max_run = 2
        raw_patterns = self._row_patterns(max_run)

        # Priorizamos máscaras con más alternancia, pero aleatorizamos las que
        # tienen la misma puntuación para que las series no sean idénticas.
        groups: dict[int, list[int]] = {}
        for mask in raw_patterns:
            groups.setdefault(self._pattern_transitions(mask), []).append(mask)

        patterns: list[int] = []
        for score in sorted(groups, reverse=True):
            group = groups[score]
            rng.shuffle(group)
            patterns.extend(group)

        pattern_set = set(patterns)

        # Pick the first two rows randomly, then derive the third row directly
        # from the required column loads. This is much faster and more reliable
        # than blind backtracking while preserving visual variety.
        for first in patterns:
            for second in patterns:
                third = 0
                valid = True
                for column, target in enumerate(counts):
                    used = ((first >> column) & 1) + ((second >> column) & 1)
                    remaining = target - used
                    if remaining not in (0, 1):
                        valid = False
                        break
                    if remaining:
                        third |= 1 << column
                if not valid or third not in pattern_set:
                    continue

                prefixes = [
                    sum(bool(mask & (1 << column)) for column in range(4))
                    for mask in (first, second, third)
                ]
                if min(prefixes) < 1 or max(prefixes) - min(prefixes) > 1:
                    continue

                # Reject an identical row mask inside one card when alternatives
                # exist; this improves the visual rhythm without changing Bingo
                # validity.
                if len({first, second, third}) < 3:
                    continue
                return [first, second, third]

        return None
