from __future__ import annotations

from pathlib import Path

from app.cards import BingoCard
from .layout import A4PrintLayout, MM_TO_PT, PrintStyle


class A4PdfRenderer:
    """Renderiza una serie de seis cartones en una página A4 PDF."""

    def __init__(self, layout: A4PrintLayout | None = None, style: PrintStyle | None = None) -> None:
        self.layout = layout or A4PrintLayout()
        self.style = style or PrintStyle()

    def save(self, cards: tuple[BingoCard, ...], path: str | Path) -> Path:
        try:
            from reportlab.lib.colors import HexColor
            from reportlab.lib.pagesizes import A4
            from reportlab.pdfbase.pdfmetrics import stringWidth
            from reportlab.pdfgen.canvas import Canvas
            from reportlab.lib.utils import ImageReader
        except ImportError as exc:  # pragma: no cover - dependency is declared by the project
            raise RuntimeError("La exportación PDF requiere reportlab") from exc

        placements = self.layout.place_cards(cards)
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        canvas = Canvas(str(destination), pagesize=A4)

        logo = None
        if self.style.logo_path:
            logo_path = Path(self.style.logo_path)
            if logo_path.is_file():
                logo = ImageReader(str(logo_path))

        for placement in placements:
            card = placement.card
            slot = placement.slot
            x = slot.x
            # Layout geometry is top-origin; ReportLab is bottom-origin.
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
                text = f"SERIE {card.serial}"
                canvas.setFillColor(HexColor(self.style.number_color))
                canvas.setFont("Helvetica", 7)
                canvas.drawRightString(x + width - 8, y + height - 13, text)

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
            footer = f"SERIAL: {card.serial}"
            canvas.drawCentredString(x + width / 2, y + 5, footer)

        canvas.showPage()
        canvas.save()
        return destination
