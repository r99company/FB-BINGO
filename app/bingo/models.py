from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .exceptions import InvalidGameStateError


MIN_BALL = 1
MAX_BALL = 90


@dataclass(frozen=True, slots=True)
class GameState:
    """Snapshot completo y serializable de una partida."""

    drawn_numbers: tuple[int, ...] = ()
    remaining_numbers: tuple[int, ...] = ()
    paused: bool = False

    def __post_init__(self) -> None:
        drawn = tuple(self.drawn_numbers)
        remaining = tuple(self.remaining_numbers)
        if len(set(drawn)) != len(drawn) or len(set(remaining)) != len(remaining):
            raise InvalidGameStateError("Los numeros no pueden repetirse")
        if any(number not in range(MIN_BALL, MAX_BALL + 1) for number in drawn + remaining):
            raise InvalidGameStateError("Los numeros deben estar entre 1 y 90")
        if set(drawn).intersection(remaining) or set(drawn).union(remaining) != set(
            range(MIN_BALL, MAX_BALL + 1)
        ):
            raise InvalidGameStateError("El estado debe contener exactamente las 90 bolas")
        object.__setattr__(self, "drawn_numbers", drawn)
        object.__setattr__(self, "remaining_numbers", remaining)

    @classmethod
    def new(cls, shuffled_numbers: tuple[int, ...]) -> "GameState":
        return cls(remaining_numbers=shuffled_numbers)

    @property
    def current_number(self) -> int | None:
        return self.drawn_numbers[-1] if self.drawn_numbers else None

    @property
    def history(self) -> tuple[int, ...]:
        return self.drawn_numbers

    @property
    def last_five(self) -> tuple[int, ...]:
        return self.drawn_numbers[-5:]

    @property
    def finished(self) -> bool:
        return not self.remaining_numbers

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        try:
            return cls(
                drawn_numbers=tuple(data["drawn_numbers"]),
                remaining_numbers=tuple(data["remaining_numbers"]),
                paused=bool(data["paused"]),
            )
        except (KeyError, TypeError, ValueError) as error:
            raise InvalidGameStateError("Datos de partida invalidos") from error