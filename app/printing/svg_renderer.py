from __future__ import annotations

import base64
from html import escape
from pathlib import Path

from app.cards import BingoCard
from app.printing.layout import A4PrintLayout, PrintStyle


class A4SvgRenderer:
    """Render one six-card series as a self-contained A4 SVG."""

    def __init__(self, layout: A4PrintLayout | None = None, style: PrintStyle | None = None):
        self.layout = layout or A4PrintLayout()
        self.style = style or PrintStyle()

    def render(self, cards: tuple[BingoCard, ...]) -> str:
        placements = self.layout.place_cards(cards)
        parts = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
            f'viewBox="0 0 {self.layout.page_width:.2f} {self.layout.page_height:.2f}">',
            f'<rect width="100%" height="100%" fill="{escape(self.style.background_color)}"/>',
        ]
        for placement in placements:
            parts.append(self._card(placement.card, placement.slot.x, placement.slot.y,
                                    placement.slot.width, placement.slot.height))
        parts.append("</svg>")
        return "\n".join(parts)

    def save(self, cards: tuple[BingoCard, ...], path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.render(cards), encoding="utf-8")
        return destination

    def _logo_href(self) -> str | None:
        if not self.style.logo_path:
            return None
        path = Path(self.style.logo_path)
        if not path.is_file():
            return None
        mime = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg"}.get(path.suffix.lower())
        if mime is None:
            return None
        data = base64.b64encode(path.read_bytes()).decode("ascii")
        return f"data:{mime};base64,{data}"

    def _card(self, card: BingoCard, x: float, y: float, width: float, height: float) -> str:
        header = 28.0
        cell_w = width / 9
        cell_h = (height - header - 14.0) / 3
        out = [
            f'<g transform="translate({x:.2f},{y:.2f})">',
            f'<rect width="{width:.2f}" height="{height:.2f}" rx="6" fill="{escape(self.style.background_color)}" '
            f'stroke="{escape(self.style.border_color)}" stroke-width="1.5"/>',
        ]
        logo = self._logo_href()
        if logo:
            out.append(f'<image href="{logo}" x="8" y="5" width="35" height="17" preserveAspectRatio="xMidYMid meet"/>')
        else:
            out.append(f'<text x="8" y="13" font-family="Arial,sans-serif" font-size="9" font-weight="bold" '
                       f'fill="{escape(self.style.accent_color)}">FB BINGO</text>')
        if self.style.show_serial:
            out.append(f'<text x="{width - 8:.2f}" y="13" text-anchor="end" font-family="Arial,sans-serif" '
                       f'font-size="7" fill="{escape(self.style.number_color)}">SERIE {escape(card.serial)}</text>')
        if self.style.show_model:
            out.append(f'<text x="8" y="23" font-family="Arial,sans-serif" font-size="6.5" '
                       f'fill="{escape(self.style.number_color)}">MODELO {escape(card.model.value)}</text>')
        for row in range(3):
            for column in range(9):
                cx = column * cell_w
                cy = header + row * cell_h
                value = card.grid[row][column]
                fill = self.style.background_color if value is not None else self.style.empty_cell_color
                out.append(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" '
                           f'fill="{escape(fill)}" stroke="{escape(self.style.border_color)}" stroke-width="0.6"/>')
                if value is not None:
                    out.append(f'<text x="{cx + cell_w/2:.2f}" y="{cy + cell_h*.67:.2f}" text-anchor="middle" '
                               f'font-family="Arial,sans-serif" font-size="13" font-weight="bold" '
                               f'fill="{escape(self.style.number_color)}">{value}</text>')
        out.append(f'<text x="{width/2:.2f}" y="{height-5:.2f}" text-anchor="middle" font-family="Arial,sans-serif" '
                   f'font-size="5.5" fill="{escape(self.style.number_color)}">SERIAL: {escape(card.serial)}</text>')
        out.append("</g>")
        return "\n".join(out)
