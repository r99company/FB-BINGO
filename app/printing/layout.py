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
    empty_cell_color: str = "#F7DDE7"
    number_color: str = "#171B2B"
    border_color: str = "#8FD9FF"
    accent_color: str = "#FF4FA3"
    secondary_accent_color: str = "#8FD9FF"
    logo_path: str | None = None
    show_model: bool = False
    show_serial: bool = True
    show_qr_zone: bool = False
    qr_caption: str = "ESCANEA PARA VERIFICAR"
    brand_title: str = "FB-BINGO"
    brand_tagline: str = "¡LA DIVERSIÓN QUE NOS UNE!"
    footer_text: str = "BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA"
    show_footer: bool = True
    show_tagline: bool = True
    font_family: str = "Arial"
    number_font_size: float = 10.0


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
    card: BingoCard
    row: int
    column: int

    @property
    def serial(self) -> str:
        return self.card.serial


@dataclass(frozen=True, slots=True)
class A4SeriesLayout:
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
    DEFAULT_CARD_WIDTH_MM = 95.0
    DEFAULT_CARD_HEIGHT_MM = 44.0
    DEFAULT_HORIZONTAL_GAP_MM = 3.0
    DEFAULT_VERTICAL_GAP_MM = 2.5

    def __init__(
        self,
        *,
        card_width_mm: float = DEFAULT_CARD_WIDTH_MM,
        card_height_mm: float = DEFAULT_CARD_HEIGHT_MM,
        horizontal_gap_mm: float = DEFAULT_HORIZONTAL_GAP_MM,
        vertical_gap_mm: float = DEFAULT_VERTICAL_GAP_MM,
    ) -> None:
        self.card_width_mm = float(card_width_mm)
        self.card_height_mm = float(card_height_mm)
        self.horizontal_gap_mm = float(horizontal_gap_mm)
        self.vertical_gap_mm = float(vertical_gap_mm)
        if self.card_width_mm <= 0 or self.card_height_mm <= 0:
            raise ValueError("El tamaño del cartón debe ser mayor que cero")
        if self.horizontal_gap_mm < 0 or self.vertical_gap_mm < 0:
            raise ValueError("La separación entre cartones no puede ser negativa")
        if 2 * self.card_width_mm + self.horizontal_gap_mm > A4_WIDTH_MM:
            raise ValueError("El ancho configurado no permite 2 columnas en A4")
        if 6 * self.card_height_mm + 5 * self.vertical_gap_mm > A4_HEIGHT_MM:
            raise ValueError("El alto configurado no permite 6 filas en A4")

        self.margin_x_mm = (A4_WIDTH_MM - 2 * self.card_width_mm - self.horizontal_gap_mm) / 2
        self.margin_y_mm = (A4_HEIGHT_MM - 6 * self.card_height_mm - 5 * self.vertical_gap_mm) / 2
        self.margin = min(self.margin_x_mm, self.margin_y_mm) * MM_TO_PT
        self.horizontal_gap = self.horizontal_gap_mm * MM_TO_PT
        self.vertical_gap = self.vertical_gap_mm * MM_TO_PT

    def card_slots(self) -> tuple[CardSlot, ...]:
        card_width = self.card_width_mm * MM_TO_PT
        card_height = self.card_height_mm * MM_TO_PT
        margin_x = self.margin_x_mm * MM_TO_PT
        margin_y = self.margin_y_mm * MM_TO_PT
        slots: list[CardSlot] = []
        index = 1
        for row in range(6):
            y = margin_y + row * (card_height + self.vertical_gap)
            for column in range(2):
                x = margin_x + column * (card_width + self.horizontal_gap)
                slots.append(CardSlot(index=index, column=column, row=row, x=x, y=y, width=card_width, height=card_height))
                index += 1
        return tuple(slots)

    def place_cards(self, cards: Sequence[BingoCard], *, duplicate_column: bool = False) -> tuple[CardPlacement, ...]:
        if len(cards) != 6:
            raise ValueError("A4 printing requires exactly 6 cards in a series")
        physical_cards = tuple(cards) + (tuple(cards) if duplicate_column else tuple())
        slots = self.card_slots()
        if len(physical_cards) > len(slots):
            raise ValueError("Too many cards for an A4 page")
        return tuple(CardPlacement(card=card, slot=slot) for card, slot in zip(physical_cards, slots))

    def place_columns(self, left: Sequence[BingoCard], right: Sequence[BingoCard] | None = None) -> tuple[CardPlacement, ...]:
        if len(left) != 6 or (right is not None and len(right) != 6):
            raise ValueError("Each A4 column requires exactly 6 cards")
        right_cards = tuple(left) if right is None else tuple(right)
        slots = self.card_slots()
        placements: list[CardPlacement] = []
        for row in range(6):
            placements.append(CardPlacement(left[row], slots[row * 2]))
            placements.append(CardPlacement(right_cards[row], slots[row * 2 + 1]))
        return tuple(placements)
