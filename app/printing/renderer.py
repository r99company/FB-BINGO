from __future__ import annotations

import base64
from html import escape
from pathlib import Path
from typing import Sequence

from app.cards import BingoCard
from .layout import A4PrintLayout, PrintStyle


def _text(value: object) -> str:
    return escape(str(value))


def _logo_data_uri(path: str | Path) -> str | None:
    logo_path = Path(path)
    if not logo_path.is_file():
        raise ValueError(f"No se encontró el logo: {logo_path}")
    suffix = logo_path.suffix.lower()
    mime_types = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".webp": "image/webp"}
    mime = mime_types.get(suffix)
    if mime is None:
        raise ValueError("El logo debe ser PNG, JPG, JPEG o WEBP")
    encoded = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def render_series_svg(
    cards: Sequence[BingoCard],
    style: PrintStyle | None = None,
    layout: A4PrintLayout | None = None,
) -> str:
    """Render exactly one six-card series as a print-ready A4 SVG preview."""
    if len(cards) != 6:
        raise ValueError("A4 printing requires exactly 6 cards per series")

    style = style or PrintStyle()
    layout = layout or A4PrintLayout()
    placements = layout.place_cards(cards)
    logo_uri = _logo_data_uri(style.logo_path) if style.logo_path else None

    parts = [
        '<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{layout.page_width:.4f}pt" height="{layout.page_height:.4f}pt" '
        f'viewBox="0 0 {layout.page_width:.4f} {layout.page_height:.4f}">',
        f'<rect width="100%" height="100%" fill="{escape(style.background_color)}"/>',
    ]

    for placement in placements:
        card = placement.card
        slot = placement.slot
        x, y, w, h = slot.x, slot.y, slot.width, slot.height
        parts.append(f'<g class="bingo-card" data-serial="{_text(card.serial)}">')
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" '
            f'fill="{escape(style.background_color)}" stroke="{escape(style.border_color)}" stroke-width="1.2"/>'
        )
        parts.append(
            f'<text x="{x + 8:.2f}" y="{y + 16:.2f}" font-family="Arial" '
            f'font-size="10" font-weight="bold" fill="{escape(style.accent_color)}">'
            f'SERIE {_text(card.serial.split("-")[0])} · CARTÓN {slot.index}</text>'
        )
        if style.show_model:
            parts.append(
                f'<text x="{x + w - 8:.2f}" y="{y + 16:.2f}" text-anchor="end" '
                f'font-family="Arial" font-size="9" fill="{escape(style.number_color)}">'
                f'MODELO {_text(card.model.value)}</text>'
            )
        if style.show_serial:
            parts.append(
                f'<text x="{x + 8:.2f}" y="{y + h - 8:.2f}" font-family="Arial" '
                f'font-size="8" fill="{escape(style.number_color)}">'
                f'SERIAL {_text(card.serial)}</text>'
            )

        grid_x = x + 8
        grid_y = y + 24
        grid_w = w - 16
        grid_h = h - 42
        cell_w = grid_w / 9
        cell_h = grid_h / 3
        logo_placed = False
        for row in range(3):
            for column in range(9):
                cx = grid_x + column * cell_w
                cy = grid_y + row * cell_h
                value = card.grid[row][column]
                is_logo_cell = logo_uri is not None and value is None and not logo_placed
                fill = style.background_color if value is not None else style.empty_cell_color
                parts.append(
                    f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" '
                    f'fill="{escape(fill)}" stroke="{escape(style.border_color)}" stroke-width="0.6"/>'
                )
                if is_logo_cell:
                    padding = min(cell_w, cell_h) * 0.12
                    parts.append(
                        f'<image href="{logo_uri}" x="{cx + padding:.2f}" y="{cy + padding:.2f}" '
                        f'width="{cell_w - 2 * padding:.2f}" height="{cell_h - 2 * padding:.2f}" '
                        f'preserveAspectRatio="xMidYMid meet"/>'
                    )
                    logo_placed = True
                elif value is not None:
                    parts.append(
                        f'<text x="{cx + cell_w / 2:.2f}" y="{cy + cell_h * 0.67:.2f}" '
                        f'text-anchor="middle" font-family="Arial" font-size="16" font-weight="bold" '
                        f'fill="{escape(style.number_color)}">{_text(value)}</text>'
                    )
        parts.append('</g>')

    parts.append('</svg>')
    return "\n".join(parts)


def save_series_svg(
    cards: Sequence[BingoCard],
    destination: str | Path,
    style: PrintStyle | None = None,
) -> Path:
    """Render and save an A4 SVG that can be previewed or converted to PDF."""
    path = Path(destination)
    path.write_text(render_series_svg(cards, style=style), encoding="utf-8")
    return path
