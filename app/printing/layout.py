from __future__ import annotations

from dataclasses import dataclass

from app.cards import BingoCard, BingoSeries


@dataclass(frozen=True, slots=True)
class PrintSlot:
    """Posición de un cartón dentro de una hoja A4."""

    card: BingoCard
    row: int
    column: int

    @property
    def serial(self) -> str:
        return self.card.serial


@dataclass(frozen=True, slots=True)
class A4SeriesLayout:
    """Distribución lógica para imprimir una serie completa en A4."""

    page_size: str
    columns: int
    cards_per_page: int
    slots: tuple[PrintSlot, ...]

    @classmethod
    def for_series(cls, series: BingoSeries) -> "A4SeriesLayout":
        slots = tuple(
            PrintSlot(card=card, row=index // 2, column=index % 2)
            for index, card in enumerate(series.cards)
        )
        return cls(page_size="A4", columns=2, cards_per_page=6, slots=slots)
