from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from typing import Sequence

from app.cards import BingoCard
from app.printing.layout import A4PrintLayout, PrintStyle


class ModernA4SvgRenderer:
    """Renderer A4 de FB-BINGO con identidad visual de sala de bingo."""

    def __init__(self, layout: A4PrintLayout | None = None, style: PrintStyle | None = None):
        self.layout = layout or A4PrintLayout()
        self.style = style or PrintStyle()

    def render(self, cards: Sequence[BingoCard], right_cards: Sequence[BingoCard] | None = None, *, duplicate_column: bool = False) -> str:
        if len(cards) != 6:
            raise ValueError("A4 printing requires exactly 6 cards in the left column")
        left = tuple(cards)
        right = left if duplicate_column else (tuple(right_cards) if right_cards is not None else None)
        placements = self.layout.place_cards(left) if right is None else self.layout.place_columns(left, right)
        parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
            f'viewBox="0 0 {self.layout.page_width:.2f} {self.layout.page_height:.2f}">',
            f'<rect width="100%" height="100%" fill="{escape(self.style.background_color)}"/>',
        ]
        for placement in placements:
            parts.append(self._card(placement.card, placement.slot.x, placement.slot.y, placement.slot.width, placement.slot.height))
        parts.append('</svg>')
        return '\n'.join(parts)

    def render_columns(self, left_cards: Sequence[BingoCard], right_cards: Sequence[BingoCard] | None = None, *, duplicate_column: bool = False) -> str:
        return self.render(left_cards, right_cards, duplicate_column=duplicate_column)

    def save(self, cards: Sequence[BingoCard], path: str | Path, right_cards: Sequence[BingoCard] | None = None, *, duplicate_column: bool = False) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(self.render(cards, right_cards, duplicate_column=duplicate_column), encoding='utf-8')
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
        header = min(21.0, height * 0.20)
        footer = min(12.0, height * 0.12)
        cell_w = width / 9
        cell_h = (height - header - footer) / 3
        logo = self._logo_href()
        serial = escape(card.serial)
        series = escape(card.serial.split('-')[0])
        card_number = escape(card.serial.split('-')[-1])
        badge_w = min(31.0, width * 0.22)
        out = [
            f'<g class="bingo-card" transform="translate({x:.2f},{y:.2f})">',
            f'<rect width="{width:.2f}" height="{height:.2f}" rx="5" fill="{escape(self.style.background_color)}" stroke="{escape(self.style.border_color)}" stroke-width="1.2"/>',
            f'<path d="M0 5 Q{width*.28:.2f} {header*.92:.2f} {width*.58:.2f} {header*.42:.2f} T{width:.2f} 4 L{width:.2f} 0 L0 0 Z" fill="{escape(self.style.accent_color)}" opacity="0.88"/>',
            f'<path d="M0 {header*.76:.2f} Q{width*.30:.2f} {header*1.04:.2f} {width*.62:.2f} {header*.66:.2f} T{width:.2f} {header*.72:.2f}" fill="none" stroke="{escape(self.style.secondary_accent_color)}" stroke-width="3" opacity="0.95"/>',
        ]
        if logo:
            out.append(f'<circle cx="14" cy="12" r="10" fill="#FFFFFF" opacity="0.96"/>')
            out.append(f'<image href="{logo}" x="5" y="3" width="18" height="18" preserveAspectRatio="xMidYMid meet"/>')
        else:
            out.append('<circle cx="14" cy="12" r="10" fill="#FFFFFF" opacity="0.96"/>')
            out.append('<text x="14" y="14.4" text-anchor="middle" font-family="Arial,sans-serif" font-size="6.4" font-weight="900" fill="#1A67B7">FB</text>')
            out.append('<text x="14" y="19" text-anchor="middle" font-family="Arial,sans-serif" font-size="3.2" font-weight="900" fill="#FF4FA3">BINGO</text>')
        out.append(f'<text x="31" y="10.5" font-family="Arial,sans-serif" font-size="6.2" font-weight="900" fill="#1764B0">FB-BINGO</text>')
        out.append(f'<text x="31" y="17" font-family="Arial,sans-serif" font-size="4.2" font-weight="bold" fill="#1764B0">¡LA DIVERSIÓN QUE NOS UNE!</text>')
        out.append(f'<rect x="{width-badge_w-5:.2f}" y="3" width="{badge_w:.2f}" height="8" rx="2.5" fill="#FF4FA3"/>')
        out.append(f'<text x="{width-badge_w/2-5:.2f}" y="8.8" text-anchor="middle" font-family="Arial,sans-serif" font-size="4.3" font-weight="900" fill="#FFFFFF">CARTÓN</text>')
        out.append(f'<text x="{width-5:.2f}" y="18.5" text-anchor="end" font-family="Arial,sans-serif" font-size="14" font-weight="900" fill="{escape(self.style.number_color)}">{card_number}</text>')
        if self.style.show_model:
            out.append(f'<text x="{width/2:.2f}" y="10.5" text-anchor="middle" font-family="Arial,sans-serif" font-size="5.2" font-weight="bold" fill="#FFFFFF">MODELO {escape(card.model.value)}</text>')
        for row in range(3):
            for column in range(9):
                cx, cy = column * cell_w, header + row * cell_h
                value = card.grid[row][column]
                if value is not None:
                    fill = self.style.background_color
                elif (row + column) % 2 == 0:
                    fill = self.style.empty_cell_color
                else:
                    fill = "#EEF8FF"
                out.append(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" rx="1.2" fill="{escape(fill)}" stroke="{escape(self.style.accent_color)}" stroke-width="0.55"/>')
                if value is not None:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.68:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" font-weight="900" fill="{escape(self.style.number_color)}">{value}</text>')
                elif (row + column) % 3 == 1:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.68:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" fill="{escape(self.style.accent_color)}">★</text>')
        out.append(f'<rect x="3" y="{height-footer:.2f}" width="{width-6:.2f}" height="{footer-1:.2f}" rx="3" fill="#F7FBFF" opacity="0.98"/>')
        out.append(f'<text x="8" y="{height-3:.2f}" font-family="Arial,sans-serif" font-size="4.1" font-weight="900" fill="#1764B0">SERIE {series}</text>')
        out.append(f'<text x="{width/2:.2f}" y="{height-3:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="3.8" font-weight="bold" fill="#1764B0">BINGO DE 90 BOLAS · JUEGA · DIVIÉRTETE · GANA</text>')
        if self.style.show_qr_zone:
            qr_size = min(13.0, footer - 1.5)
            qr_x, qr_y = width - qr_size - 5, height - qr_size - 1.5
            out.append(f'<rect class="qr-zone" x="{qr_x:.2f}" y="{qr_y:.2f}" width="{qr_size:.2f}" height="{qr_size:.2f}" fill="#FFFFFF" stroke="{escape(self.style.accent_color)}" stroke-width="0.8"/>')
            out.append(f'<path d="M{qr_x+2:.2f} {qr_y+2:.2f}h3v3h-3z M{qr_x+7:.2f} {qr_y+2:.2f}h3v3h-3z M{qr_x+2:.2f} {qr_y+7:.2f}h3v3h-3z M{qr_x+7:.2f} {qr_y+7:.2f}h2v2h-2z" fill="#111827"/>')
        if self.style.show_serial:
            out.append(f'<text x="{width-5:.2f}" y="{height-3:.2f}" text-anchor="end" font-family="Arial,sans-serif" font-size="3.2" fill="#1764B0">ID: {serial}</text>')
        out.append('</g>')
        return '\n'.join(out)
