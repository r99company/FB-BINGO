from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from typing import Sequence

from app.cards import BingoCard
from app.printing.layout import A4PrintLayout, PrintStyle


class ModernA4SvgRenderer:
    """Renderer A4 de FB-BINGO con distribución de 2 columnas x 6 filas."""

    def __init__(self, layout: A4PrintLayout | None = None, style: PrintStyle | None = None):
        self.layout = layout or A4PrintLayout()
        self.style = style or PrintStyle()

    def render(
        self,
        cards: Sequence[BingoCard],
        right_cards: Sequence[BingoCard] | None = None,
        *,
        duplicate_column: bool = False,
    ) -> str:
        if len(cards) != 6:
            raise ValueError("A4 printing requires exactly 6 cards in the left column")
        left = tuple(cards)
        right = left if duplicate_column else (tuple(right_cards) if right_cards is not None else None)
        if right is None:
            placements = self.layout.place_cards(left)
        else:
            placements = self.layout.place_columns(left, right)

        parts = [
            '<svg xmlns="http://www.w3.org/2000/svg" width="210mm" height="297mm" '
            f'viewBox="0 0 {self.layout.page_width:.2f} {self.layout.page_height:.2f}">',
            f'<rect width="100%" height="100%" fill="{escape(self.style.background_color)}"/>',
        ]
        for placement in placements:
            parts.append(
                self._card(
                    placement.card,
                    placement.slot.x,
                    placement.slot.y,
                    placement.slot.width,
                    placement.slot.height,
                )
            )
        parts.append('</svg>')
        return '\n'.join(parts)

    def render_columns(
        self,
        left_cards: Sequence[BingoCard],
        right_cards: Sequence[BingoCard] | None = None,
        *,
        duplicate_column: bool = False,
    ) -> str:
        """Render a production page: left 1–6 and right 7–12, or duplicate left."""
        return self.render(left_cards, right_cards, duplicate_column=duplicate_column)

    def save(
        self,
        cards: Sequence[BingoCard],
        path: str | Path,
        right_cards: Sequence[BingoCard] | None = None,
        *,
        duplicate_column: bool = False,
    ) -> Path:
        destination = Path(path)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            self.render(cards, right_cards, duplicate_column=duplicate_column),
            encoding='utf-8',
        )
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
        out = [
            f'<g class="bingo-card" transform="translate({x:.2f},{y:.2f})">',
            f'<rect width="{width:.2f}" height="{height:.2f}" rx="5" fill="{escape(self.style.background_color)}" '
            f'stroke="{escape(self.style.border_color)}" stroke-width="1.4"/>',
            f'<rect width="{width:.2f}" height="{header:.2f}" rx="5" fill="{escape(self.style.secondary_accent_color)}"/>',
        ]
        if logo:
            out.append(f'<image href="{logo}" x="5" y="3" width="34" height="14" preserveAspectRatio="xMidYMid meet"/>')
        else:
            out.append('<text x="5" y="11" font-family="Arial,sans-serif" font-size="7" font-weight="900" fill="#FFFFFF">FB-BINGO</text>')
        if self.style.show_model:
            out.append(
                f'<text x="{width/2:.2f}" y="10.5" text-anchor="middle" font-family="Arial,sans-serif" '
                f'font-size="5.2" font-weight="bold" fill="#FFFFFF">MODELO {escape(card.model.value)}</text>'
            )
        out.append(f'<text x="{width-5:.2f}" y="10.5" text-anchor="end" font-family="Arial,sans-serif" font-size="5.2" font-weight="bold" fill="#FFFFFF">SERIE {series} · CARTÓN {card_number}</text>')
        for row in range(3):
            for column in range(9):
                cx, cy = column * cell_w, header + row * cell_h
                value = card.grid[row][column]
                fill = self.style.background_color if value is not None else self.style.empty_cell_color
                out.append(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" fill="{escape(fill)}" stroke="{escape(self.style.border_color)}" stroke-width="0.55"/>')
                if value is not None:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.68:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="10" font-weight="900" fill="{escape(self.style.number_color)}">{value}</text>')
        if self.style.show_qr_zone:
            qr_size = min(9.0, footer - 2.0)
            qr_x, qr_y = width - qr_size - 5, height - qr_size - 2
            out.append(f'<rect class="qr-zone" x="{qr_x:.2f}" y="{qr_y:.2f}" width="{qr_size:.2f}" height="{qr_size:.2f}" fill="#FFFFFF" stroke="{escape(self.style.accent_color)}" stroke-width="0.8"/>')
        if self.style.show_serial:
            out.append(f'<text x="{width/2:.2f}" y="{height-3:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="4.2" fill="{escape(self.style.number_color)}">SERIAL: {serial}</text>')
        out.append('</g>')
        return '\n'.join(out)
