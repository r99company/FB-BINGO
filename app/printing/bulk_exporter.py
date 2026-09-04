from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.cards import BingoSeries, CardModel
from .layout import PrintStyle
from .svg_renderer import A4SvgRenderer

CARDS_PER_SERIES = 6


class SeriesRepository(Protocol):
    def get(self, series_id: str) -> BingoSeries: ...


@dataclass(frozen=True, slots=True)
class BulkA4ExportResult:
    pages_exported: int
    cards_exported: int
    first_series: int
    last_series: int
    destination: Path


class BulkA4SvgExporter:
    """Exporta cada serie como una hoja A4 SVG independiente y lista para imprimir."""

    def __init__(self, repository: SeriesRepository, style: PrintStyle | None = None) -> None:
        self.repository = repository
        self.style = style or PrintStyle()
        self.renderer = A4SvgRenderer(style=self.style)

    def export(
        self,
        *,
        start_series: int,
        quantity: int,
        destination: str | Path,
        model: CardModel | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> BulkA4ExportResult:
        if start_series < 1 or quantity < 1:
            raise ValueError("La serie inicial y la cantidad deben ser positivos")

        output = Path(destination)
        output.mkdir(parents=True, exist_ok=True)
        last_series = start_series + quantity - 1

        for offset in range(quantity):
            number = start_series + offset
            series = self.repository.get(str(number))
            if model is not None and any(card.model is not model for card in series.cards):
                raise ValueError(f"La serie {number} no coincide con el modelo seleccionado")
            if len(series.cards) != CARDS_PER_SERIES:
                raise ValueError(f"La serie {number} no contiene exactamente 6 cartones")

            target = output / f"serie_{number:04d}.svg"
            self.renderer.save(series.cards, target)
            if progress is not None:
                progress(offset + 1, quantity)

        return BulkA4ExportResult(
            pages_exported=quantity,
            cards_exported=quantity * CARDS_PER_SERIES,
            first_series=start_series,
            last_series=last_series,
            destination=output,
        )
