from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class BingoSession:
    """Estado de una partida de bingo de 90 bolas."""

    game_name: str = "Partida rápida"
    called_numbers: list[int] = field(default_factory=list)
    active: bool = False

    def start(self) -> None:
        self.called_numbers.clear()
        self.active = True

    def call(self, number: int) -> None:
        if not 1 <= number <= 90:
            raise ValueError("La bola debe estar entre 1 y 90")
        if not self.active:
            raise RuntimeError("La partida no está activa")
        if number in self.called_numbers:
            raise ValueError(f"La bola {number} ya fue cantada")
        self.called_numbers.append(number)

    def stop(self) -> None:
        self.active = False

    @property
    def last_five(self) -> tuple[int, ...]:
        return tuple(self.called_numbers[-5:])

    def has_number(self, number: int) -> bool:
        return number in self.called_numbers

    def is_winner(self, numbers: list[int] | tuple[int, ...]) -> bool:
        return bool(numbers) and all(number in self.called_numbers for number in numbers)
