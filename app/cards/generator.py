from __future__ import annotations

from dataclasses import dataclass
import hashlib
import random
from typing import Sequence

from .card import BingoCard, CardModel, COLUMNS, ROWS, NUMBERS_PER_CARD
from .distribution import CARDS_PER_SERIES, DistributionModel

MAX_SERIAL = 30_000


@dataclass(frozen=True, slots=True)
class BingoSeries:
    """Serie física de seis cartones que cubre una vez los números 1-90."""
    series_id: str
    cards: tuple[BingoCard, ...]

    def __post_init__(self) -> None:
        if not str(self.series_id).strip():
            raise ValueError("El identificador de serie es obligatorio")
        if len(self.cards) != CARDS_PER_SERIES:
            raise ValueError("Una serie debe contener exactamente 6 cartones")
        numbers = [number for card in self.cards for number in card.numbers]
        if len(numbers) != 90 or set(numbers) != set(range(1, 91)):
            raise ValueError("Los 6 cartones de la serie deben cubrir 1-90 exactamente una vez")
        if len({card.serial for card in self.cards}) != CARDS_PER_SERIES:
            raise ValueError("Los seriales de una serie deben ser únicos")


class SeriesGenerator:
    """Generador determinista: una serie siempre conserva su misma matriz."""

    def __init__(self, seed: int | None = None, max_serial: int = MAX_SERIAL) -> None:
        if max_serial < CARDS_PER_SERIES:
            raise ValueError("max_serial no permite completar una serie")
        self._seed = 0 if seed is None else int(seed)
        self._rng = random.Random(seed)
        self._max_serial = max_serial

    def _series_rng(self, series_id: str) -> random.Random:
        material = f"FB-BINGO|{self._seed}|{series_id}".encode("utf-8")
        seed = int.from_bytes(hashlib.sha256(material).digest()[:16], "big")
        return random.Random(seed)

    def generate(self, series_id: str, model: CardModel = CardModel.A, serial_start: int = 1) -> BingoSeries:
        series_id = str(series_id).strip()
        if not series_id:
            raise ValueError("El identificador de serie es obligatorio")
        if serial_start < 1:
            raise ValueError("serial_start debe ser positivo")
        if serial_start + CARDS_PER_SERIES - 1 > self._max_serial:
            raise ValueError(f"Una serie no puede superar el serial {self._max_serial}")

        rng = self._series_rng(series_id)
        distribution = DistributionModel.for_model(model)
        best_grids = None
        best_score = -10**9
        for _ in range(192):
            column_counts = self._column_counts(model, distribution, rng)
            grids = self._build_grids(column_counts, distribution, rng, aesthetic=False)
            if grids is None:
                continue
            score = self._dynamic_layout_score(grids, column_counts)
            if score > best_score:
                best_score, best_grids = score, grids
        if best_grids is None:
            raise RuntimeError("No se pudo generar una serie válida después de varios intentos")

        return BingoSeries(
            series_id=series_id,
            cards=tuple(
                BingoCard(serial=f"{series_id}-{serial_start + index:06d}", model=model, grid=grid)
                for index, grid in enumerate(best_grids)
            ),
        )

    @staticmethod
    def _row_signature(grid: Sequence[Sequence[int | None]], row: int) -> tuple[bool, ...]:
        return tuple(grid[row][column] is not None for column in range(COLUMNS))

    @staticmethod
    def _card_mask_signature(grid: Sequence[Sequence[int | None]]) -> tuple[tuple[bool, ...], ...]:
        return tuple(tuple(grid[row][column] is not None for column in range(COLUMNS)) for row in range(ROWS))

    @staticmethod
    def _column_signature(counts: Sequence[int]) -> tuple[int, ...]:
        return tuple(counts)

    @classmethod
    def _pair_distance(cls, first, second) -> int:
        return sum(cls._hamming(first[row], second[row]) for row in range(ROWS))

    @classmethod
    def _dynamic_layout_score(cls, grids, column_counts=None) -> int:
        score = 0
        signatures = [[cls._row_signature(grid, row) for row in range(ROWS)] for grid in grids]
        full_masks = [cls._card_mask_signature(grid) for grid in grids]
        score += len(set(full_masks)) * 900
        pair_distances = []
        for left in range(len(full_masks)):
            for right in range(left + 1, len(full_masks)):
                distance = cls._pair_distance(full_masks[left], full_masks[right])
                pair_distances.append(distance)
                score += distance * 14
                if distance == 0:
                    score -= 8_000
                elif distance < 8:
                    score -= (8 - distance) * 450
                elif distance >= 10:
                    score += (distance - 9) * 35
        if pair_distances:
            score += min(pair_distances) * 180
            score += sorted(pair_distances)[1] * 60
        for row in range(ROWS):
            weight = 7 if row == 1 else 5
            for left in range(len(signatures)):
                for right in range(left + 1, len(signatures)):
                    score += cls._hamming(signatures[left][row], signatures[right][row]) * weight
        for group in signatures:
            zones = (
                sum(mask[c] for mask in group for c in range(0, 3)),
                sum(mask[c] for mask in group for c in range(3, 6)),
                sum(mask[c] for mask in group for c in range(6, 9)),
            )
            score -= (max(zones) - min(zones)) * 2
            for signature in group:
                run = longest = 0
                for occupied in signature:
                    run = run + 1 if occupied else 0
                    longest = max(longest, run)
                score -= max(0, longest - 2) * 10
        if column_counts is not None:
            column_signatures = [cls._column_signature(counts) for counts in column_counts]
            score += len(set(column_signatures)) * 40
            for index in range(1, len(column_signatures)):
                if column_signatures[index] == column_signatures[index - 1]:
                    score -= 50
            for left in range(len(column_signatures)):
                for right in range(left + 1, len(column_signatures)):
                    if column_signatures[left] == column_signatures[right]:
                        score -= 12
        return score

    @staticmethod
    def _hamming(a, b) -> int:
        return sum(x != y for x, y in zip(a, b))

    @staticmethod
    def _column_counts(model, distribution=None, rng=None):
        """Única fuente de verdad para la ocupación de columnas."""
        distribution = distribution or DistributionModel.for_model(model)
        rng = rng or random.Random()
        return distribution.column_counts(rng)

    def _build_grids(self, column_counts, distribution=None, rng=None, aesthetic=True):
        distribution = distribution or DistributionModel.for_model(CardModel.A)
        rng = rng or self._rng
        row_masks = []
        for counts in column_counts:
            masks = distribution.row_masks_for_counts(counts, rng)
            if masks is None or any(mask.bit_count() != 5 for mask in masks):
                return None
            if any(sum(bool(mask & (1 << column)) for mask in masks) != counts[column] for column in range(COLUMNS)):
                return None
            row_masks.append(masks)
        grids = [[[None for _ in range(COLUMNS)] for _ in range(ROWS)] for _ in range(CARDS_PER_SERIES)]
        for column in range(COLUMNS):
            values = list(self._values_for_column(column)); rng.shuffle(values); cursor = 0
            for card_index in range(CARDS_PER_SERIES):
                count = column_counts[card_index][column]
                card_values = sorted(values[cursor:cursor + count]); cursor += count
                rows = [row for row in range(ROWS) if row_masks[card_index][row] & (1 << column)]
                if len(card_values) != count or len(rows) != count:
                    return None
                for value_index, row in enumerate(rows):
                    grids[card_index][row][column] = card_values[value_index]
            if cursor != len(values):
                return None
        result = [tuple(tuple(row) for row in grid) for grid in grids]
        if aesthetic and len({self._card_mask_signature(grid) for grid in result}) < 2:
            return None
        return result

    @staticmethod
    def _values_for_column(column: int) -> range:
        start = 1 if column == 0 else column * 10
        end = 9 if column == 0 else (column + 1) * 10 - 1
        if column == 8:
            end = 90
        return range(start, end + 1)
