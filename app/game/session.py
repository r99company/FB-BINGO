from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class GameSession:
    """Estado en memoria de una partida de Bingo de 90 bolas."""

    name: str = "Partida rápida"
    called: list[int] = field(default_factory=list)
    active: bool = False

    def start(self) -> None:
        self.called.clear()
        self.active = True

    def call(self, number: int) -> None:
        if not 1 <= number <= 90:
            raise ValueError("La bola debe estar entre 1 y 90")
        if not self.active:
            raise RuntimeError("La partida no está activa")
        if number in self.called:
            raise ValueError(f"La bola {number} ya fue cantada")
        self.called.append(number)

    def undo(self) -> int:
        if not self.called:
            raise ValueError("No hay bolas para deshacer")
        return self.called.pop()

    @property
    def last_five(self) -> list[int]:
        return self.called[-5:]

    @property
    def called_set(self) -> set[int]:
        return set(self.called)

    def reset(self, name: str | None = None) -> None:
        self.called.clear()
        if name is not None:
            self.name = name
        self.active = True

    def stop(self) -> None:
        self.active = False


class BingoSession(GameSession):
    """API compatible con el estado histórico de Bingo 90."""

    @property
    def called_numbers(self) -> list[int]:
        return self.called

    @property
    def last_five(self) -> tuple[int, ...]:
        return tuple(self.called[-5:])

    def has_number(self, number: int) -> bool:
        return number in self.called

    def is_winner(self, numbers: list[int] | tuple[int, ...] | set[int]) -> bool:
        return bool(numbers) and set(numbers).issubset(self.called_set)
