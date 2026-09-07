from __future__ import annotations

import random

from .exceptions import GameFinishedError, GamePausedError
from .models import MAX_BALL, MIN_BALL, GameState


class BingoGame:
    """Motor de Bingo exclusivamente para 90 bolas, numeradas del 1 al 90."""

    def __init__(self, seed: int | None = None) -> None:
        self._random = random.Random(seed)
        self._initial_random_state = self._random.getstate()
        self._state = self._new_state()

    def _new_state(self) -> GameState:
        numbers = list(range(MIN_BALL, MAX_BALL + 1))
        self._random.shuffle(numbers)
        return GameState.new(tuple(numbers))

    @property
    def state(self) -> GameState:
        return self._state

    @property
    def current_number(self) -> int | None:
        return self._state.current_number

    @property
    def history(self) -> tuple[int, ...]:
        return self._state.history

    @property
    def last_five(self) -> tuple[int, ...]:
        return self._state.last_five

    def draw(self) -> int:
        if self._state.paused:
            raise GamePausedError("La partida esta pausada")
        if self._state.finished:
            raise GameFinishedError("Ya se han sorteado las 90 bolas")
        return self._record_number(self._state.remaining_numbers[0])

    def call_manual(self, number: int) -> int:
        """Registra la bola extraída físicamente por la locutora."""
        if self._state.paused:
            raise GamePausedError("La partida esta pausada")
        if self._state.finished:
            raise GameFinishedError("Ya se han sorteado las 90 bolas")
        if not isinstance(number, int) or isinstance(number, bool) or not MIN_BALL <= number <= MAX_BALL:
            raise ValueError("La bola debe estar entre 1 y 90")
        if number in self._state.drawn_numbers:
            raise ValueError(f"La bola {number} ya fue cantada")
        return self._record_number(number)

    def _record_number(self, number: int) -> int:
        remaining = tuple(n for n in self._state.remaining_numbers if n != number)
        self._state = GameState(
            drawn_numbers=self._state.drawn_numbers + (number,),
            remaining_numbers=remaining,
            paused=False,
        )
        return number

    def pause(self) -> None:
        if not self._state.finished:
            self._state = GameState(
                drawn_numbers=self._state.drawn_numbers,
                remaining_numbers=self._state.remaining_numbers,
                paused=True,
            )

    def resume(self) -> None:
        if self._state.paused:
            self._state = GameState(
                drawn_numbers=self._state.drawn_numbers,
                remaining_numbers=self._state.remaining_numbers,
                paused=False,
            )

    def reset(self) -> None:
        self._random.setstate(self._initial_random_state)
        self._state = self._new_state()

    def restore(self, state: GameState) -> None:
        """Restaura estado sin permitir que una mutación accidental quite la pausa."""
        if self._state.paused and not state.paused:
            state = GameState(
                drawn_numbers=state.drawn_numbers,
                remaining_numbers=state.remaining_numbers,
                paused=True,
            )
        self._state = state

    @classmethod
    def from_state(cls, state: GameState, seed: int | None = None) -> "BingoGame":
        game = cls(seed=seed)
        game.restore(state)
        return game
