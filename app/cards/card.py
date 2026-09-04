from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Iterable

ROWS = 3
COLUMNS = 9
NUMBERS_PER_CARD = 15


class CardModel(StrEnum):
    """Modelo visual/estructural usado al imprimir el cartón."""

    A = "A"
    B = "B"


Grid = tuple[tuple[int | None, ...], ...]


def _column_range(column: int) -> range:
    if column < 0 or column >= COLUMNS:
        raise ValueError("Columna fuera de rango")
    start = 1 if column == 0 else column * 10
    end = 9 if column == 0 else (column + 1) * 10 - 1
    if column == 8:
        end = 90
    return range(start, end + 1)


@dataclass(frozen=True, slots=True)
class BingoCard:
    """Cartón de Bingo de 90 bolas con su matriz exacta y modelo de impresión."""

    serial: str
    model: CardModel
    grid: Grid

    def __post_init__(self) -> None:
        if not self.serial or not self.serial.strip():
            raise ValueError("El serial del cartón es obligatorio")
        if not isinstance(self.model, CardModel):
            raise ValueError("El modelo del cartón no es válido")
        if len(self.grid) != ROWS or any(len(row) != COLUMNS for row in self.grid):
            raise ValueError("El cartón debe tener una matriz de 3 x 9")

        numbers: list[int] = []
        for row in self.grid:
            if sum(value is not None for value in row) != 5:
                raise ValueError("Cada fila debe contener exactamente 5 números")

        for column in range(COLUMNS):
            values = [self.grid[row][column] for row in range(ROWS)]
            count = sum(value is not None for value in values)
            if not 1 <= count <= 3:
                raise ValueError("Cada columna debe contener entre 1 y 3 números")
            previous = [value for value in values if value is not None]
            if previous != sorted(previous):
                raise ValueError("Los números de cada columna deben estar ordenados")
            allowed = _column_range(column)
            if any(value not in allowed for value in previous):
                raise ValueError("Hay un número fuera del rango de su columna")
            numbers.extend(previous)

        if len(numbers) != NUMBERS_PER_CARD:
            raise ValueError("El cartón debe contener exactamente 15 números")
        if len(set(numbers)) != NUMBERS_PER_CARD:
            raise ValueError("Un cartón no puede repetir números")

    @property
    def numbers(self) -> frozenset[int]:
        return frozenset(
            value for row in self.grid for value in row if value is not None
        )

    @property
    def column_counts(self) -> tuple[int, ...]:
        return tuple(
            sum(self.grid[row][column] is not None for row in range(ROWS))
            for column in range(COLUMNS)
        )

    def row_numbers(self, row: int) -> tuple[int, ...]:
        if row not in range(ROWS):
            raise IndexError("Fila fuera de rango")
        return tuple(value for value in self.grid[row] if value is not None)

    def is_marked(self, row: int, column: int, called_numbers: Iterable[int]) -> bool:
        value = self.grid[row][column]
        return value is not None and value in set(called_numbers)
