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
    puntuación y elección aleatoria entre muchas soluciones válidas. Así no
    sacrificamos generación por intentar imponer una sola máscara "bonita".
    """

    model: CardModel

    @classmethod
    def for_model(cls, model: CardModel) -> "DistributionModel":
        if not isinstance(model, CardModel):
            raise ValueError("El modelo de distribución no es válido")
        return cls(model=model)

    def column_counts(self, rng: random.Random) -> list[list[int]]:
        """Reparte 90 posiciones entre 6 cartones de forma equilibrada.

        Cada columna del 1-9, 10-19, ... 80-90 aporta 9, 10 u 11 números a
        la serie. Cada cartón recibe exactamente 15 números y, en A, nunca
        más de dos por columna.
        """
        targets = [9] + [10] * 7 + [11]
        result = [[1] * COLUMNS for _ in range(CARDS_PER_SERIES)]
        loads = [0] * CARDS_PER_SERIES

        columns = list(range(COLUMNS))
        rng.shuffle(columns)
        for column in columns:
            extra = targets[column] - CARDS_PER_SERIES
            order = list(range(CARDS_PER_SERIES))
            rng.shuffle(order)
            # Elegimos primero los cartones con menor carga y mezclamos los
            # empates. Esto mantiene 15 números por cartón sin crear un orden
            # fijo de máscaras entre series.
            order.sort(key=lambda i: (loads[i], rng.random()))
            for card_index in order[:extra]:
                result[card_index][column] += 1
                loads[card_index] += 1

        if loads != [6] * CARDS_PER_SERIES:
            raise RuntimeError("No se pudo equilibrar la distribución de la serie")
        return result

    @staticmethod
    def _row_patterns(max_run: int) -> list[int]:
        patterns: list[int] = []
        for mask in range(1 << COLUMNS):
            if mask.bit_count() != 5:
                continue

            longest = current = 0
            for column in range(COLUMNS):
                if mask & (1 << column):
                    current += 1
                    longest = max(longest, current)
                else:
                    current = 0
            if longest > max_run:
                continue
            patterns.append(mask)
        return patterns

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
        """Puntuación estética, nunca una regla de validez."""
        score = sum(cls._transitions(mask) for mask in triple) * 5

        # Preferimos que las cuatro primeras columnas y las cuatro últimas
        # tengan presencia repartida entre las tres filas, pero sin exigirlo.
        prefix = [sum(bool(mask & (1 << c)) for c in range(4)) for mask in triple]
        suffix = [sum(bool(mask & (1 << c)) for c in range(5, 9)) for mask in triple]
        score -= (max(prefix) - min(prefix)) * 3
        score -= (max(suffix) - min(suffix)) * 3

        # Recompensa una distribución menos "en bloque" en el centro.
        center = [sum(bool(mask & (1 << c)) for c in range(2, 7)) for mask in triple]
        score -= sum(abs(value - 3) for value in center)
        return score

    def row_masks_for_counts(
        self,
        counts: Sequence[int],
        rng: random.Random,
        forbidden: Sequence[set[int]] | None = None,
    ) -> list[int] | None:
        if len(counts) != COLUMNS or sum(counts) != NUMBERS_PER_CARD:
            return None

        max_per_column = 2 if self.model is CardModel.A else 3
        if any(count < 1 or count > max_per_column for count in counts):
            return None

        # Modelo A busca un patrón muy aireado (máximo 2 consecutivos). Para B
        # permitimos hasta 3, porque su propia definición admite columnas más
        # cargadas y no queremos deformar artificialmente la distribución.
        max_run = 2 if self.model is CardModel.A else 3
        patterns = self._row_patterns(max_run)
        rng.shuffle(patterns)

        if forbidden is None:
            forbidden = [set(), set(), set()]

        best: tuple[int, tuple[int, int, int]] | None = None
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

                if not valid or third.bit_count() != 5 or third not in set(patterns):
                    continue

                triple = (first, second, third)
                if len(set(triple)) != 3:
                    continue
                if any(triple[row] in forbidden[row] for row in range(3)):
                    continue

                score = self._triple_score(triple)
                # Añadimos ruido pequeño para que dos series con la misma
                # calidad visual no terminen escogiendo siempre el mismo patrón.
                score = score * 100 + rng.randrange(100)
                if best is None or score > best[0]:
                    best = (score, triple)

        return list(best[1]) if best is not None else None
