from __future__ import annotations

from dataclasses import dataclass
import itertools
import random
from typing import Sequence

from .card import COLUMNS, CardModel

CARDS_PER_SERIES = 6
NUMBERS_PER_CARD = 15


@dataclass(frozen=True, slots=True)
class DistributionModel:
    """Reglas de ocupación de casillas para un cartón de Bingo 90.

    Las reglas matemáticas son estrictas; la variedad visual se obtiene
    muestreando un número limitado de soluciones válidas. Nunca se enumeran
    todas las combinaciones posibles, porque eso hacía que la generación de
    muchas series fuese innecesariamente lenta.
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
        columns = list(range(COLUMNS))
        rng.shuffle(columns)
        for column in columns:
            extra = targets[column] - CARDS_PER_SERIES
            order = list(range(CARDS_PER_SERIES))
            rng.shuffle(order)
            order.sort(key=lambda i: (loads[i], rng.random()))
            for card_index in order[:extra]:
                result[card_index][column] += 1
                loads[card_index] += 1
        if loads != [6] * CARDS_PER_SERIES:
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

    def row_masks_for_counts(
        self,
        counts: Sequence[int],
        rng: random.Random,
        forbidden: Sequence[set[int]] | None = None,
    ) -> list[int] | None:
        """Construye tres máscaras de cinco casillas con las cargas dadas.

        La búsqueda está acotada: obtiene varias soluciones válidas y escoge
        la de mejor apariencia entre ellas. Esto conserva la variedad de los
        cartones de referencia sin bloquear la generación de series.
        """
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None
        max_per_column = 2 if self.model is CardModel.A else 3
        if any(count < 1 or count > max_per_column for count in counts):
            return None
        if forbidden is None:
            forbidden = [set(), set(), set()]

        columns = sorted(range(COLUMNS), key=lambda c: (-counts[c], rng.random()))
        best_score: int | None = None
        best_triple: tuple[int, int, int] | None = None

        def find_one() -> tuple[int, int, int] | None:
            remaining = [5, 5, 5]
            masks = [0, 0, 0]

            def recurse(position: int) -> bool:
                if position == len(columns):
                    return remaining == [0, 0, 0] and not any(
                        masks[row] in forbidden[row] for row in range(3)
                    )

                column = columns[position]
                count = counts[column]
                choices = list(itertools.combinations(range(3), count))
                rng.shuffle(choices)
                future = len(columns) - position - 1

                for rows in choices:
                    if any(remaining[row] <= 0 for row in rows):
                        continue
                    for row in rows:
                        remaining[row] -= 1
                        masks[row] |= 1 << column

                    # Cada fila debe poder consumir exactamente las casillas
                    # que faltan en las columnas todavía no asignadas.
                    feasible = all(0 <= value <= future for value in remaining)
                    if feasible and recurse(position + 1):
                        return True

                    for row in rows:
                        remaining[row] += 1
                        masks[row] &= ~(1 << column)
                return False

            return tuple(masks) if recurse(0) else None

        # Con cargas de 1/2 (Modelo A) y 1/3 (Modelo B), encontrar una solución
        # es pequeño; limitamos los intentos para que generar miles de series
        # sea predecible en tiempo.
        for _ in range(24):
            triple = find_one()
            if triple is None:
                break
            if len(set(triple)) < 2 and best_triple is not None:
                continue
            score = self._triple_score(triple) * 100 + rng.randrange(100)
            if best_score is None or score > best_score:
                best_score = score
                best_triple = triple

        if best_triple is not None:
            return list(best_triple)
        return None
