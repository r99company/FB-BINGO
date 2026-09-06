from __future__ import annotations

from dataclasses import dataclass

from app.cards.card import BingoCard


@dataclass(frozen=True, slots=True)
class VerificationResult:
    serial: str
    valid: bool
    line_complete: bool
    bingo_complete: bool
    missing: tuple[int, ...]


class CardVerifier:
    """Verifica un cartón contra las bolas cantadas de una partida."""

    def verify(self, card: BingoCard, called: set[int] | frozenset[int]) -> VerificationResult:
        called_set = set(called)
        missing = tuple(sorted(card.numbers - called_set))
        row_complete = any(all(value in called_set for value in card.row_numbers(row)) for row in range(3))
        bingo_complete = not missing
        return VerificationResult(
            serial=card.serial,
            valid=line_complete := row_complete or bingo_complete,
            line_complete=row_complete,
            bingo_complete=bingo_complete,
            missing=missing,
        )
