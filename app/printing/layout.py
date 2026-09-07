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
    show_qr_zone: bool = False
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
    """Physical A4 geometry: two columns by six rows (12 physical cards)."""

    page_width = A4_WIDTH_MM * MM_TO_PT
    page_height = A4_HEIGHT_MM * MM_TO_PT
    margin = 7.0 * MM_TO_PT
    horizontal_gap = 3.0 * MM_TO_PT
    vertical_gap = 2.5 * MM_TO_PT

    def card_slots(self) -> tuple[CardSlot, ...]:
        inner_width = self.page_width - 2 * self.margin
        inner_height = self.page_height - 2 * self.margin
        card_width = (inner_width - self.horizontal_gap) / 2
        card_height = (inner_height - 5 * self.vertical_gap) / 6
        slots: list[CardSlot] = []
        index = 1
        for row in range(6):
            y = self.margin + row * (card_height + self.vertical_gap)
            for column in range(2):
                x = self.margin + column * (card_width + self.horizontal_gap)
                slots.append(CardSlot(index=index, column=column, row=row, x=x, y=y, width=card_width, height=card_height))
                index += 1
        return tuple(slots)

    def place_cards(
        self,
        cards: Sequence[BingoCard],
        *,
        duplicate_column: bool = False,
    ) -> tuple[CardPlacement, ...]:
        if len(cards) != 6:
            raise ValueError("A4 printing requires exactly 6 cards in a series")
        physical_cards = tuple(cards) + (tuple(cards) if duplicate_column else tuple(cards))
        if not duplicate_column:
            # Normal production advances the right column to the next six cards.
            # The renderer can supply those cards when printing a continuous batch;
            # a single-series preview remains intentionally six physical cards.
            physical_cards = tuple(cards)
        slots = self.card_slots()
        if len(physical_cards) > len(slots):
            raise ValueError("Too many cards for an A4 page")
        return tuple(CardPlacement(card=card, slot=slot) for card, slot in zip(physical_cards, slots))

    def place_columns(self, left: Sequence[BingoCard], right: Sequence[BingoCard] | None = None) -> tuple[CardPlacement, ...]:
        """Place six cards in the left column and six in the right column."""
        if len(left) != 6 or (right is not None and len(right) != 6):
            raise ValueError("Each A4 column requires exactly 6 cards")
        right_cards = tuple(left) if right is None else tuple(right)
        cards = tuple(left) + tuple(right_cards)
        slots = self.card_slots()
        placements: list[CardPlacement] = []
        for row in range(6):
            placements.append(CardPlacement(cards[row], slots[row * 2]))
            placements.append(CardPlacement(cards[6 + row], slots[row * 2 + 1]))
        return tuple(placements)
