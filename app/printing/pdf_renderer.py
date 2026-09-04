from __future__ import annotations

from pathlib import Path
from typing import Callable, Protocol

from app.cards import BingoCard, BingoSeries, CardModel
from .layout import A4PrintLayout, PrintStyle


class SeriesRepository(Protocol):
    def get(self, series_id: str) -> BingoSeries: ...


class A4PdfRenderer:
    """Renderiza cartones A4 y puede escribir muchas series en un único PDF."""

    def __init__(self, layout: A4PrintLayout | None = None, style: PrintStyle | None = None) -> None:
        self.layout = layout or A4PrintLayout()
        self.style = style or PrintStyle()

    @staticmethod
    def _dependencies():
        try:
            from reportlab.lib.colors import HexColor
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase.pdfmetrics import stringWidth
            from reportlab.pdfgen.canvas import Canvas
            from reportlab.lib.utils import ImageReader
        except ImportError as exc:  # pragma: no cover - dependency is declared by the project
            raise RuntimeError("La exportación PDF requiere reportlab") from exc
        return HexColor, A4, stringWidth, Canvas, ImageReader

    def save(self, cards: tuple[BingoCard, ...], path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _, _, _, Canvas, _ = self._dependencies()
        canvas = Canvas(str(destination), pagesize=(self.layout.page_width, self.layout.page_height))
        self._draw_page(canvas, cards)
        canvas.showPage()
        canvas.save()
        return destination

    def export_pages(
        self,
        *,
        repository: SeriesRepository,
        start_series: int,
        quantity: int,
        destination: str | Path,
        model: CardModel | None = None,
        progress: Callable[[int, int], None] | None = None,
    ) -> Path:
        """Escribe una página A4 por serie, manteniendo memoria constante."""
        if start_series < 1 or quantity < 1:
            raise ValueError("La serie inicial y la cantidad deben ser positivos")
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)
        _, _, _, Canvas, _ = self._dependencies()
        canvas = Canvas(str(destination), pagesize=(self.layout.page_width, self.layout.page_height))
        try:
            for offset in range(quantity):
                number = start_series + offset
                series = repository.get(str(number))
                if model is not None and any(card.model is not model for card in series.cards):
                    raise ValueError(f"La serie {number} no coincide con el modelo seleccionado")
                self._draw_page(canvas, series.cards)
                canvas.showPage()
                if progress is not None:
                    progress(offset + 1, quantity)
        finally:
            canvas.save()
        return destination

    def _draw_page(self, canvas, cards: tuple[BingoCard, ...]) -> None:
        HexColor, _, stringWidth, _, ImageReader = self._dependencies()
        placements = self.layout.place_cards(cards)
        logo = None
        if self.style.logo_path:
            logo_path = Path(self.style.logo_path)
            if logo_path.is_file():
                logo = ImageReader(str(logo_path))

        canvas.setFillColor(HexColor(self.style.background_color))
        canvas.rect(0, 0, self.layout.page_width, self.layout.page_height, fill=1, stroke=0)

        for placement in placements:
            card = placement.card
            slot = placement.slot
            x = slot.x
            y = self.layout.page_height - slot.y - slot.height
            width, height = slot.width, slot.height
            header = 28.0
            cell_w = width / 9
            cell_h = (height - header - 14.0) / 3

            canvas.setFillColor(HexColor(self.style.background_color))
            canvas.setStrokeColor(HexColor(self.style.border_color))
            canvas.roundRect(x, y, width, height, 6, fill=1, stroke=1)

            canvas.setFillColor(HexColor(self.style.accent_color))
            canvas.setFont("Helvetica-Bold", 9)
            canvas.drawString(x + 8, y + height - 13, "FB BINGO")

            if self.style.show_serial:
                canvas.setFillColor(HexColor(self.style.number_color))
                canvas.setFont("Helvetica", 7)
                canvas.drawRightString(x + width - 8, y + height - 13, f"SERIE {card.serial}")

            if self.style.show_model:
                canvas.setFillColor(HexColor(self.style.number_color))
                canvas.setFont("Helvetica", 6.5)
                canvas.drawString(x + 8, y + height - 23, f"MODELO {card.model.value}")

            logo_placed = False
            for row in range(3):
                for column in range(9):
                    cx = x + column * cell_w
                    cy = y + height - header - (row + 1) * cell_h
                    value = card.grid[row][column]
                    fill = self.style.background_color if value is not None else self.style.empty_cell_color
                    canvas.setFillColor(HexColor(fill))
                    canvas.setStrokeColor(HexColor(self.style.border_color))
                    canvas.rect(cx, cy, cell_w, cell_h, fill=1, stroke=1)
                    if value is not None:
                        text = str(value)
                        canvas.setFillColor(HexColor(self.style.number_color))
                        canvas.setFont("Helvetica-Bold", 13)
                        tw = stringWidth(text, "Helvetica-Bold", 13)
                        canvas.drawString(cx + (cell_w - tw) / 2, cy + cell_h * 0.33, text)
                    elif logo and not logo_placed:
                        padding = min(cell_w, cell_h) * 0.12
                        canvas.drawImage(
                            logo,
                            cx + padding,
                            cy + padding,
                            width=cell_w - 2 * padding,
                            height=cell_h - 2 * padding,
                            preserveAspectRatio=True,
                            anchor="c",
                            mask="auto",
                        )
                        logo_placed = True

            canvas.setFillColor(HexColor(self.style.number_color))
            canvas.setFont("Helvetica", 5.5)
            canvas.drawCentredString(x + width / 2, y + 5, f"SERIAL: {card.serial}")
