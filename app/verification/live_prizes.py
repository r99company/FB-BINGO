from __future__ import annotations

from dataclasses import dataclass

from app.cards import BingoCard
from app.database import SQLiteSeriesRepository


@dataclass(frozen=True, slots=True)
class LivePrize:
    serial: str
    series_id: str
    card_index: int
    line_rows: tuple[int, ...] = ()
    bingo: bool = False

    @property
    def kind(self) -> str:
        return "BINGO" if self.bingo else "LÍNEA"


class LivePrizeTracker:
    """Detecta premios potenciales en tiempo real sin recorrer 30.000 cartones por bola."""

    def __init__(self, repository: SQLiteSeriesRepository, max_cards: int = 30_000) -> None:
        self.repository = repository
        self.max_cards = max_cards
        self._cards: dict[str, BingoCard] = {}
        self._series_position: dict[str, tuple[str, int]] = {}
        self._number_index: dict[int, list[tuple[str, int]]] = {number: [] for number in range(1, 91)}
        self._remaining_card: dict[str, int] = {}
        self._remaining_rows: dict[tuple[str, int], int] = {}
        self._line_rows: dict[str, set[int]] = {}
        self._bingo: set[str] = set()
        self._called: set[int] = set()
        self._loaded = False

    @staticmethod
    def _position_from_serial(serial: str) -> tuple[str, int]:
        if "-" in serial:
            series_id, suffix = serial.rsplit("-", 1)
            if suffix.isdigit():
                number = int(suffix)
                return series_id, ((number - 1) % 6) + 1
        return "—", 0

    def load(self) -> None:
        total = min(self.repository.count_cards(), self.max_cards)
        self._reset_state()
        if total <= 0:
            self._loaded = True
            return
        cards = self.repository.get_cards_range(1, total)
        for card in cards:
            self._cards[card.serial] = card
            self._series_position[card.serial] = self._position_from_serial(card.serial)
            self._remaining_card[card.serial] = 15
            self._line_rows[card.serial] = set()
            for row_index, row in enumerate(card.grid):
                values = [value for value in row if value is not None]
                self._remaining_rows[(card.serial, row_index)] = len(values)
                for value in values:
                    self._number_index[value].append((card.serial, row_index))
        self._loaded = True

    def _reset_state(self) -> None:
        self._cards.clear()
        self._series_position.clear()
        self._number_index = {number: [] for number in range(1, 91)}
        self._remaining_card.clear()
        self._remaining_rows.clear()
        self._line_rows.clear()
        self._bingo.clear()
        self._called.clear()

    def reset(self, called_numbers: set[int] | frozenset[int] = frozenset()) -> None:
        if not self._loaded:
            if called_numbers:
                self.load()
            else:
                return
        self._remaining_card = {serial: 15 for serial in self._cards}
        self._remaining_rows = {
            (serial, row): sum(value is not None for value in card.grid[row])
            for serial, card in self._cards.items()
            for row in range(3)
        }
        self._line_rows = {serial: set() for serial in self._cards}
        self._bingo.clear()
        self._called.clear()
        for number in sorted(called_numbers):
            self.add_ball(number)

    def add_ball(self, number: int) -> None:
        if not self._loaded:
            self.load()
        if number in self._called:
            return
        if not 1 <= number <= 90:
            raise ValueError("La bola debe estar entre 1 y 90")
        self._called.add(number)
        touched: set[str] = set()
        for serial, row in self._number_index[number]:
            remaining = self._remaining_rows[(serial, row)]
            if remaining <= 0:
                continue
            self._remaining_rows[(serial, row)] = remaining - 1
            self._remaining_card[serial] -= 1
            touched.add(serial)
        for serial in touched:
            for row in range(3):
                if self._remaining_rows[(serial, row)] == 0:
                    self._line_rows[serial].add(row + 1)
            if self._remaining_card[serial] == 0:
                self._bingo.add(serial)

    def update(self, called_numbers: set[int] | frozenset[int]) -> None:
        called = set(called_numbers)
        if not self._loaded:
            if not called:
                return
            self.load()
        if called < self._called:
            self.reset(called)
            return
        for number in sorted(called - self._called):
            self.add_ball(number)

    def prizes(self, *, include_bingo: bool = True) -> tuple[LivePrize, ...]:
        result: list[LivePrize] = []
        for serial, rows in self._line_rows.items():
            bingo = serial in self._bingo
            if rows or (include_bingo and bingo):
                series_id, card_index = self._series_position[serial]
                result.append(LivePrize(serial, series_id, card_index, tuple(sorted(rows)), bingo))
        result.sort(key=lambda item: (not item.bingo, int(item.serial[-6:]) if item.serial[-6:].isdigit() else item.serial))
        return tuple(result)

    def line_winners(self) -> tuple[LivePrize, ...]:
        return tuple(prize for prize in self.prizes(include_bingo=False) if not prize.bingo)

    def bingo_winners(self) -> tuple[LivePrize, ...]:
        return tuple(prize for prize in self.prizes(include_bingo=True) if prize.bingo)

    @property
    def called_count(self) -> int:
        return len(self._called)
