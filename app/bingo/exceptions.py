class BingoError(Exception):
    """Base para errores del motor de Bingo."""


class InvalidGameStateError(BingoError, ValueError):
    """El estado de una partida no cumple las reglas de Bingo de 90 bolas."""


class GamePausedError(BingoError, RuntimeError):
    """Se intento sortear mientras la partida estaba pausada."""


class GameFinishedError(BingoError, RuntimeError):
    """Se intento sortear cuando ya salieron las 90 bolas."""