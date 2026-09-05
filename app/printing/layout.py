from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from app.cards import BingoCard, BingoSeries

MM_TO_PT = 72 / 25.4
A4_WIDTH_MM = 210.0
A4_HEIGHT_MM = 297.0


@dataclass(frozen=True, slots=True)
class PrintStyle:
    """Visual settings for printed cards; game logic never depends on these."""

    background_color: str = "#FFFFFF"
    empty_cell_color: str = "#F2E9FF"
    number_color: str = "#171B2B"
    border_color: str = "#7D6BFF"
    accent_color: str = "#FF4FA3"
    secondary_accent_color: str = "#8FD9FF"
    logo_path: str | None = None
    show_model: bool = True
    show_serial: bool = True
    show_qr_zone: bool = True
    qr_caption: str = "ESCANEA PARA VERIFICAR"


@dataclass(frozen=True, slots=True)
class CardSlot:
    index: int
    column: int
    row: int
    x: float
    y: float
    width: float
    height: float

    def intersects(self, other: "CardSlot") -> bool:
        return not (self.x + self.width <= other.x or other.x + other.width <= self.x or self.y + self.height <= other.y or other.y + other.height <= self.y)


@dataclass(frozen=True, slots=True)
class CardPlacement:
    card: BingoCard
    slot: CardSlot


@dataclass(frozen=True, slots=True)
class PrintSlot:
    """Backward-compatible logical position of a card inside an A4 page."""

    card: BingoCard
    row: int
    column: int

    @property
    def serial(self) -> str:
        return self.card.serial


@dataclass(frozen=True, slots=True)
class A4SeriesLayout:
    """Logical distribution for one complete six-card series."""

    page_size: str
    columns: int
    cards_per_page: int
    slots: tuple[PrintSlot, ...]

    @classmethod
    def for_series(cls, series: BingoSeries) -> "A4SeriesLayout":
        slots = tuple(PrintSlot(card=card, row=index // 2, column=index % 2) for index, card in enumerate(series.cards))
        return cls(page_size="A4", columns=2, cards_per_page=6, slots=slots)


class A4PrintLayout:
    """Physical A4 geometry: two columns by three rows."""

    page_width = A4_WIDTH_MM * MM_TO_PT
    page_height = A4_HEIGHT_MM * MM_TO_PT
    margin = 12.0 * MM_TO_PT
    horizontal_gap = 5.0 * MM_TO_PT
    vertical_gap = 5.0 * MM_TO_PT

    def card_slots(self) -> tuple[CardSlot, ...]:
        inner_width = self.page_width - 2 * self.margin
        inner_height = self.page_height - 2 * self.margin
        card_width = (inner_width - self.horizontal_gap) / 2
        card_height = (inner_height - 2 * self.vertical_gap) / 3
        slots: list[CardSlot] = []
        index = 1
        for row in range(3):
            y = self.margin + row * (card_height + self.vertical_gap)
            height = card_height if row < 2 else self.page_height - self.margin - y
            for column in range(2):
                x = self.margin + column * (card_width + self.horizontal_gap)
                width = card_width if column == 0 else self.page_width - self.margin - x
                slots.append(CardSlot(index=index, column=column, row=row, x=x, y=y, width=width, height=height))
                index += 1
        return tuple(slots)

    def place_cards(self, cards: Sequence[BingoCard]) -> tuple[CardPlacement, ...]:
        if len(cards) != 6:
            raise ValueError("A4 printing requires exactly 6 cards per series")
        return tuple(CardPlacement(card=card, slot=slot) for card, slot in zip(cards, self.card_slots()))
