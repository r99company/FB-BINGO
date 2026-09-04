from __future__ import annotations

from dataclasses import dataclass

from app.cards import BingoCard


@dataclass(frozen=True)
class VerificationResult:
    serial: str
    model: str
    line_rows: tuple[int, ...]
    bingo: bool

    @property
    def has_prize(self) -> bool:
        return bool(self.line_rows) or self.bingo


class CardCheckService:
    """Verifica un cartón almacenado usando su matriz real y las bolas llamadas."""

    @staticmethod
    def check(card: BingoCard, called_numbers: set[int] | frozenset[int]) -> VerificationResult:
        called = set(called_numbers)
        if any(number < 1 or number > 90 for number in called):
            raise ValueError("Las bolas llamadas deben estar entre 1 y 90")

        rows = tuple(
            row_index
            for row_index in range(3)
            if all(
                value is None or value in called
                for value in card.grid[row_index]
            )
            and any(value is not None for value in card.grid[row_index])
        )
        bingo = card.numbers.issubset(called)
        return VerificationResult(
            serial=card.serial,
            model=card.model.value,
            line_rows=rows,
            bingo=bingo,
        )
