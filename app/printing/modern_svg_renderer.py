from __future__ import annotations

import base64
from html import escape
from pathlib import Path

from app.cards import BingoCard
from app.printing.layout import A4PrintLayout, PrintStyle


class ModernA4SvgRenderer:
    """Renderer A4 de FB-BINGO con identidad visual, logo y zona QR."""

    def __init__(self, layout: A4PrintLayout | None = None, style: PrintStyle | None = None):
        self.layout = layout or A4PrintLayout()
        self.style = style or PrintStyle()

    def render(self, cards: tuple[BingoCard, ...]) -> str:
        if len(cards) != 6:
            raise ValueError("A4 printing requires exactly 6 cards per series")
        parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
            f'viewBox="0 0 {self.layout.page_width:.2f} {self.layout.page_height:.2f}">',
            f'<rect width="100%" height="100%" fill="{escape(self.style.background_color)}"/>',
        ]
        for placement in self.layout.place_cards(cards):
            parts.append(self._card(placement.card, placement.slot.x, placement.slot.y,
                                    placement.slot.width, placement.slot.height))
        parts.append('</svg>')
        return '\n'.join(parts)

    def save(self, cards: tuple[BingoCard, ...], path: str | Path) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.render(cards), encoding='utf-8')
        return destination

    def _logo_href(self) -> str | None:
        if not self.style.logo_path:
            return None
        path = Path(self.style.logo_path)
        if not path.is_file():
            return None
        mime = {'.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg'}.get(path.suffix.lower())
        if not mime:
            return None
        encoded = base64.b64encode(path.read_bytes()).decode('ascii')
        return f'data:{mime};base64,{encoded}'

    def _card(self, card: BingoCard, x: float, y: float, width: float, height: float) -> str:
        header = 30.0
        footer = 27.0 if self.style.show_qr_zone else 14.0
        cell_w = width / 9
        cell_h = (height - header - footer) / 3
        logo = self._logo_href()
        serial = escape(card.serial)
        series = escape(card.serial.split('-')[0])
        card_number = escape(card.serial.split('-')[-1])
        out = [
            f'<g transform="translate({x:.2f},{y:.2f})">',
            f'<rect width="{width:.2f}" height="{height:.2f}" rx="8" fill="{escape(self.style.background_color)}" '
            f'stroke="{escape(self.style.border_color)}" stroke-width="1.8"/>',
            f'<rect width="{width:.2f}" height="{header:.2f}" rx="8" fill="{escape(self.style.secondary_accent_color)}"/>',
        ]
        if logo:
            out.append(f'<image href="{logo}" x="8" y="5" width="42" height="20" preserveAspectRatio="xMidYMid meet"/>')
        else:
            out.append('<text x="8" y="14" font-family="Arial,sans-serif" font-size="10" font-weight="900" fill="#FFFFFF">FB-BINGO</text>')
        out.append(f'<text x="{width-8:.2f}" y="13" text-anchor="end" font-family="Arial,sans-serif" font-size="7" font-weight="bold" fill="#FFFFFF">SERIE {series} · CARTÓN {card_number}</text>')
        for row in range(3):
            for column in range(9):
                cx, cy = column * cell_w, header + row * cell_h
                value = card.grid[row][column]
                fill = self.style.background_color if value is not None else self.style.empty_cell_color
                out.append(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" fill="{escape(fill)}" stroke="{escape(self.style.border_color)}" stroke-width="0.7"/>')
                if value is not None:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.67:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="14" font-weight="900" fill="{escape(self.style.number_color)}">{value}</text>')
        if self.style.show_qr_zone:
            qr_size = min(19.0, footer - 6.0)
            qr_x, qr_y = width - qr_size - 8, height - qr_size - 4
            out.append(f'<rect x="{qr_x:.2f}" y="{qr_y:.2f}" width="{qr_size:.2f}" height="{qr_size:.2f}" rx="3" fill="#FFFFFF" stroke="{escape(self.style.accent_color)}" stroke-width="1"/>')
            mark = qr_size * .23
            for mx, my in ((qr_x+2, qr_y+2), (qr_x+qr_size-mark-2, qr_y+2), (qr_x+2, qr_y+qr_size-mark-2)):
                out.append(f'<rect x="{mx:.2f}" y="{my:.2f}" width="{mark:.2f}" height="{mark:.2f}" fill="#171B2B"/>')
                out.append(f'<rect x="{mx+2:.2f}" y="{my+2:.2f}" width="{mark-4:.2f}" height="{mark-4:.2f}" fill="#FFFFFF"/>')
            out.append(f'<text x="8" y="{height-14:.2f}" font-family="Arial,sans-serif" font-size="6.3" font-weight="800" fill="{escape(self.style.accent_color)}">{escape(self.style.qr_caption)}</text>')
            out.append(f'<text x="8" y="{height-5:.2f}" font-family="Arial,sans-serif" font-size="5.5" fill="{escape(self.style.number_color)}">SERIAL {serial}</text>')
        else:
            out.append(f'<text x="{width/2:.2f}" y="{height-5:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="5.5" fill="{escape(self.style.number_color)}">SERIAL: {serial}</text>')
        out.append('</g>')
        return '\n'.join(out)
