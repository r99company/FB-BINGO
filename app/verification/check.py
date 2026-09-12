from __future__ import annotations

from dataclasses import dataclass

from app.cards import BingoCard

from .verifier import CardVerifier


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
    """Compatibilidad de servicio: delega la regla de premio al verificador único."""

    @staticmethod
    def check(card: BingoCard, called_numbers: set[int] | frozenset[int]) -> VerificationResult:
        verifier = CardVerifier(card)
        line_rows = verifier.line_winners(called_numbers)
        bingo = verifier.is_bingo(called_numbers)
        return VerificationResult(
            serial=card.serial,
            model=card.model.value,
            line_rows=line_rows,
            bingo=bingo,
        )
