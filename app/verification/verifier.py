from __future__ import annotations

from collections.abc import Iterable

from app.cards import BingoCard


class CardVerifier:
    """Comprueba premios usando la matriz exacta del cartón, no su modelo."""

    def __init__(self, card: BingoCard) -> None:
        self.card = card

    @staticmethod
    def _called(called_numbers: Iterable[int]) -> frozenset[int]:
        called = frozenset(called_numbers)
        if any(number not in range(1, 91) for number in called):
            raise ValueError("Los números llamados deben estar entre 1 y 90")
        return called

    def row_complete(self, row: int, called_numbers: Iterable[int]) -> bool:
        called = self._called(called_numbers)
        row_values = self.card.row_numbers(row)
        return bool(row_values) and all(number in called for number in row_values)

    def line_winners(self, called_numbers: Iterable[int]) -> tuple[int, ...]:
        called = self._called(called_numbers)
        return tuple(
            row for row in range(3) if self.row_complete(row, called)
        )

    def is_line(self, called_numbers: Iterable[int]) -> bool:
        return bool(self.line_winners(called_numbers))

    def is_bingo(self, called_numbers: Iterable[int]) -> bool:
        called = self._called(called_numbers)
        return self.card.numbers.issubset(called)
