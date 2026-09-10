from __future__ import annotations

from dataclasses import dataclass
import random
from typing import Sequence

from .card import COLUMNS, CardModel

CARDS_PER_SERIES = 6
NUMBERS_PER_CARD = 15


@dataclass(frozen=True, slots=True)
class DistributionModel:
    """Reglas de ocupación de casillas para un cartón de Bingo 90.

    Las reglas matemáticas son estrictas; la estética se resuelve mediante
    puntuación y elección aleatoria entre muchas soluciones válidas.
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

        En lugar de recorrer cientos de miles de pares de máscaras, se hace
        una pequeña búsqueda por columnas. Esto mantiene la variedad visual
        sin convertir la generación en un cuello de botella.
        """
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None
        max_per_column = 2 if self.model is CardModel.A else 3
        if any(count < 1 or count > max_per_column for count in counts):
            return None
        if forbidden is None:
            forbidden = [set(), set(), set()]

        # Las columnas más cargadas primero reducen mucho el espacio de búsqueda.
        columns = sorted(range(COLUMNS), key=lambda c: (-counts[c], rng.random()))
        remaining = [5, 5, 5]
        masks = [0, 0, 0]
        best: tuple[int, tuple[int, int, int]] | None = None

        def recurse(position: int) -> None:
            nonlocal best
            if position == len(columns):
                if remaining != [0, 0, 0]:
                    return
                triple = tuple(masks)
                if any(triple[row] in forbidden[row] for row in range(3)):
                    return
                if len(set(triple)) < 2:
                    # Se evita repetir las tres filas completas cuando existe
                    # otra solución; no es una regla matemática del cartón.
                    return
                score = self._triple_score(triple) * 100 + rng.randrange(100)
                if best is None or score > best[0]:
                    best = (score, triple)
                return

            column = columns[position]
            count = counts[column]
            choices = list(__import__("itertools").combinations(range(3), count))
            rng.shuffle(choices)
            for rows in choices:
                if any(remaining[row] <= 0 for row in rows):
                    continue
                for row in rows:
                    remaining[row] -= 1
                    masks[row] |= 1 << column
                # Poda: cada fila debe poder completar exactamente 5.
                future = len(columns) - position - 1
                feasible = all(0 <= value <= future for value in remaining)
                if feasible:
                    recurse(position + 1)
                for row in rows:
                    remaining[row] += 1
                    masks[row] &= ~(1 << column)

        recurse(0)
        if best is not None:
            return list(best[1])

        # Fallback: en el improbable caso de que la preferencia de variedad
        # elimine la única forma posible, devolvemos cualquier solución válida.
        remaining = [5, 5, 5]
        masks = [0, 0, 0]
        result: list[int] | None = None

        def fallback(position: int) -> bool:
            nonlocal result
            if position == len(columns):
                if remaining == [0, 0, 0]:
                    result = list(masks)
                    return True
                return False
            column = columns[position]
            choices = list(__import__("itertools").combinations(range(3), counts[column]))
            rng.shuffle(choices)
            for rows in choices:
                if any(remaining[row] <= 0 for row in rows):
                    continue
                for row in rows:
                    remaining[row] -= 1
                    masks[row] |= 1 << column
                future = len(columns) - position - 1
                feasible = all(0 <= value <= future for value in remaining)
                ok = feasible and fallback(position + 1)
                for row in rows:
                    remaining[row] += 1
                    masks[row] &= ~(1 << column)
                if ok:
                    return True
            return False

        return result if fallback(0) else None
