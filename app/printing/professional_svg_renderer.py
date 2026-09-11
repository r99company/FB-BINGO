from __future__ import annotations

from html import escape

from app.printing.modern_svg_renderer import ModernA4SvgRenderer


class ProfessionalA4SvgRenderer(ModernA4SvgRenderer):
    """Renderizador físico alineado con la referencia visual aprobada de FB-BINGO."""

    def _card(self, card, x: float, y: float, width: float, height: float) -> str:
        style = self.style
        header = min(18.0, height * 0.34)
        footer = min(8.5, height * 0.18) if style.show_footer else 2.0
        grid_top = header + 1.7
        grid_bottom = height - footer - 1.5
        gap_x = min(0.75, max(0.45, width / 150.0))
        gap_y = min(0.9, max(0.55, height / 55.0))
        cell_w = (width - gap_x * 8 - 1.2) / 9
        cell_h = (grid_bottom - grid_top - gap_y * 2) / 3
        font = escape(style.font_family)
        number_size = max(8.0, min(13.5, float(style.number_font_size) + 1.5))
        serial = escape(card.serial)
        series = escape(card.serial.split('-')[0])
        card_number = escape(card.serial.split('-')[-1])
        logo = self._logo_href()
        out = [
            f'<g class="bingo-card" transform="translate({x:.2f},{y:.2f})">',
            f'<rect width="{width:.2f}" height="{height:.2f}" rx="4.2" fill="#FFFFFF" stroke="#D8E4EE" stroke-width="0.8"/>',
            f'<path d="M0 0 H{width:.2f} V{header*.72:.2f} C{width*.76:.2f} {header*.54:.2f} {width*.64:.2f} {header*1.02:.2f} {width*.48:.2f} {header*.80:.2f} C{width*.30:.2f} {header*.54:.2f} {width*.17:.2f} {header*.96:.2f} 0 {header*.68:.2f} Z" fill="#F38FB5"/>',
            f'<path d="M0 {header*.66:.2f} C{width*.20:.2f} {header*.88:.2f} {width*.37:.2f} {header*.56:.2f} {width*.53:.2f} {header*.76:.2f} C{width*.70:.2f} {header*.97:.2f} {width*.85:.2f} {header*.60:.2f} {width:.2f} {header*.70:.2f} V{header*.88:.2f} C{width*.80:.2f} {header*.77:.2f} {width*.63:.2f} {header*1.06:.2f} {width*.47:.2f} {header*.84:.2f} C{width*.30:.2f} {header*.62:.2f} {width*.14:.2f} {header*.96:.2f} 0 {header*.78:.2f} Z" fill="#A8DCF8" opacity="0.95"/>',
        ]
        if logo:
            out.append(f'<circle cx="13.5" cy="12" r="9.0" fill="#FFFFFF" opacity="0.98"/>')
            out.append(f'<image href="{logo}" x="5.0" y="3.4" width="17" height="17" preserveAspectRatio="xMidYMid meet"/>')
        else:
            out.append('<circle cx="13.5" cy="12" r="9" fill="#FFFFFF" opacity="0.98"/>')
            out.append('<text x="13.5" y="13.4" text-anchor="middle" font-family="Arial,sans-serif" font-size="6.4" font-weight="900" fill="#1971C2">FB</text>')
            out.append('<text x="13.5" y="18" text-anchor="middle" font-family="Arial,sans-serif" font-size="2.8" font-weight="900" fill="#EC4B91">BINGO</text>')
        out.append(f'<text x="26" y="10.5" font-family="{font},Arial,sans-serif" font-size="5.8" font-weight="900" fill="#1971C2">FB-<tspan fill="#E94C91">BINGO</tspan></text>')
        if style.show_tagline:
            out.append(f'<text x="26" y="16.1" font-family="{font},Arial,sans-serif" font-size="3.25" font-weight="800" fill="#1971C2">{escape(style.brand_tagline)}</text>')

        badge_x = width - 40.0
        out.append(f'<rect x="{badge_x:.2f}" y="2.4" width="17.5" height="5.0" rx="2" fill="#EC5A98"/>')
        out.append(f'<text x="{badge_x+8.75:.2f}" y="6.15" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="3.3" font-weight="900" fill="#FFFFFF">CARTÓN</text>')
        out.append(f'<text x="{width-20:.2f}" y="14.6" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="12.5" font-weight="900" fill="#10264A">{card_number}</text>')

        if style.show_qr_zone:
            qr_size = min(13.5, max(11.0, header - 4.0))
            qr_x = width - qr_size - 3.0
            qr_y = 1.0
            out.append(f'<rect x="{qr_x:.2f}" y="{qr_y:.2f}" width="{qr_size:.2f}" height="{qr_size:.2f}" rx="1.0" fill="#FFFFFF" stroke="#D7E5EF" stroke-width="0.5"/>')
            q = qr_x + 1.0
            s = qr_size - 2.0
            out.append(f'<rect x="{q:.2f}" y="{qr_y+1:.2f}" width="4.0" height="4.0" fill="#101820"/><rect x="{q+0.9:.2f}" y="{qr_y+1.9:.2f}" width="2.2" height="2.2" fill="#FFFFFF"/>')
            out.append(f'<rect x="{q+s-4:.2f}" y="{qr_y+1:.2f}" width="4.0" height="4.0" fill="#101820"/><rect x="{q+s-3.1:.2f}" y="{qr_y+1.9:.2f}" width="2.2" height="2.2" fill="#FFFFFF"/>')
            out.append(f'<rect x="{q:.2f}" y="{qr_y+s-5:.2f}" width="4.0" height="4.0" fill="#101820"/><rect x="{q+0.9:.2f}" y="{qr_y+s-4.1:.2f}" width="2.2" height="2.2" fill="#FFFFFF"/>')
            for dx, dy, ww, hh in ((5,2,2,2),(8,5,2,2),(5,8,2,2),(9,9,1.8,1.8),(7,11,2,1.5),(11,7,1.5,2),(6,6,1.2,1.2)):
                out.append(f'<rect x="{q+dx:.2f}" y="{qr_y+dy:.2f}" width="{ww:.2f}" height="{hh:.2f}" fill="#101820"/>')

        for row in range(3):
            for column in range(9):
                cx = 0.8 + column * (cell_w + gap_x)
                cy = grid_top + row * (cell_h + gap_y)
                value = card.grid[row][column]
                if value is not None:
                    fill = "#FFFFFF"
                elif (row + column) % 2 == 0:
                    fill = "#FCE7EF"
                else:
                    fill = "#EAF6FC"
                out.append(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" rx="1.6" fill="{fill}" stroke="#F08AB1" stroke-width="0.48"/>')
                if value is not None:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.68:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="{number_size:.1f}" font-weight="900" fill="#10264A">{value}</text>')
                elif (row * 2 + column) % 4 == 1:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.69:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="{max(6.5, number_size*.9):.1f}" font-weight="700" fill="#EE8DB4">☆</text>')

        if style.show_footer:
            fy = height - footer + 0.2
            out.append(f'<rect x="1.2" y="{fy:.2f}" width="{width-2.4:.2f}" height="{footer-0.8:.2f}" rx="2.2" fill="#F4FAFE"/>')
            out.append(f'<rect x="3" y="{fy+0.8:.2f}" width="24" height="{max(4.0, footer-2):.2f}" rx="2" fill="#ED4D91"/>')
            out.append(f'<text x="15" y="{height-2.4:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="3.0" font-weight="900" fill="#FFFFFF">SERIE {series}</text>')
            out.append(f'<text x="{width*.49:.2f}" y="{height-2.5:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="3.0" font-weight="900" fill="#23618D">BINGO DE 90 BOLAS</text>')
            out.append(f'<text x="{width-27:.2f}" y="{height-2.5:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="3.0" font-weight="900" fill="#23618D">JUEGA · DIVIÉRTETE · GANA</text>')
        if style.show_serial:
            out.append(f'<text x="{width-1.8:.2f}" y="{height/2:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="2.2" fill="#23618D" transform="rotate(-90 {width-1.8:.2f} {height/2:.2f})">ID: {serial}</text>')
        out.append('</g>')
        return '\n'.join(out)


__all__ = ["ProfessionalA4SvgRenderer"]
