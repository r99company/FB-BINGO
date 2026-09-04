from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.cards import BingoSeries, CardModel
from .layout import PrintStyle
from .pdf_renderer import A4PdfRenderer

CARDS_PER_SERIES = 6


class SeriesRepository(Protocol):
    def get(self, series_id: str) -> BingoSeries: ...


@dataclass(frozen=True, slots=True)
class BulkA4PdfExportResult:
    pages_exported: int
    cards_exported: int
    first_series: int
    last_series: int
    destination: Path


class BulkA4PdfExporter:
    """Genera un único PDF A4 con una página por serie, sin acumularlas en memoria."""

    def __init__(self, repository: SeriesRepository, style: PrintStyle | None = None) -> None:
        self.repository = repository
        self.style = style or PrintStyle()

    def export(
        self,
        *,
        start_series: int,
        quantity: int,
        destination: str | Path,
        model: CardModel | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> BulkA4PdfExportResult:
        if start_series < 1 or quantity < 1:
            raise ValueError("La serie inicial y la cantidad deben ser positivos")

        output = Path(destination)
        output.parent.mkdir(parents=True, exist_ok=True)
        renderer = A4PdfRenderer(style=self.style)

        # Render each page into its own temporary PDF, then merge would add an
        # unnecessary dependency. Instead the renderer is extended below to a
        # multi-page writer through its stream API.
        renderer.export_pages(
            repository=self.repository,
            start_series=start_series,
            quantity=quantity,
            destination=output,
            model=model,
            progress=progress,
        )

        return BulkA4PdfExportResult(
            pages_exported=quantity,
            cards_exported=quantity * CARDS_PER_SERIES,
            first_series=start_series,
            last_series=start_series + quantity - 1,
            destination=output,
        )
