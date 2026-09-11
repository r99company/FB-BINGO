from __future__ import annotations

from html import escape

from app.printing.modern_svg_renderer import ModernA4SvgRenderer


class ProfessionalA4SvgRenderer(ModernA4SvgRenderer):
    """Renderizador físico alineado con la referencia visual aprobada de FB-BINGO."""

    def _card(self, card, x: float, y: float, width: float, height: float) -> str:
        style = self.style
        header = min(36.0, height * 0.29)
        footer = min(16.0, height * 0.15) if style.show_footer else 2.0
        grid_top = header + 2.0
        grid_bottom = height - footer - 2.0
        gap_x = min(2.0, max(1.1, width / 190.0))
        gap_y = min(2.4, max(1.4, height / 55.0))
        cell_w = (width - gap_x * 8 - 2.0) / 9
        cell_h = (grid_bottom - grid_top - gap_y * 2) / 3
        font = escape(style.font_family)
        number_size = max(10.0, min(15.0, float(style.number_font_size) + 3.0))
        serial = escape(card.serial)
        series = escape(card.serial.split('-')[0])
        card_number = escape(card.serial.split('-')[-1])
        logo = self._logo_href()
        out = [
            f'<g class="bingo-card" transform="translate({x:.2f},{y:.2f})">',
            f'<rect width="{width:.2f}" height="{height:.2f}" rx="5" fill="#FFFFFF" stroke="#D8E4EE" stroke-width="1.0"/>',
            f'<path d="M0 0 H{width:.2f} V{header*.72:.2f} C{width*.76:.2f} {header*.54:.2f} {width*.64:.2f} {header*1.02:.2f} {width*.48:.2f} {header*.80:.2f} C{width*.30:.2f} {header*.54:.2f} {width*.17:.2f} {header*.96:.2f} 0 {header*.68:.2f} Z" fill="#F38FB5"/>',
            f'<path d="M0 {header*.66:.2f} C{width*.20:.2f} {header*.88:.2f} {width*.37:.2f} {header*.56:.2f} {width*.53:.2f} {header*.76:.2f} C{width*.70:.2f} {header*.97:.2f} {width*.85:.2f} {header*.60:.2f} {width:.2f} {header*.70:.2f} V{header*.88:.2f} C{width*.80:.2f} {header*.77:.2f} {width*.63:.2f} {header*1.06:.2f} {width*.47:.2f} {header*.84:.2f} C{width*.30:.2f} {header*.62:.2f} {width*.14:.2f} {header*.96:.2f} 0 {header*.78:.2f} Z" fill="#A8DCF8" opacity="0.96"/>',
        ]
        if logo:
            out.append('<circle cx="18" cy="18" r="14.5" fill="#FFFFFF" opacity="0.98"/>')
            out.append(f'<image href="{logo}" x="4" y="4" width="28" height="28" preserveAspectRatio="xMidYMid meet"/>')
        else:
            out.append('<circle cx="18" cy="18" r="14.5" fill="#FFFFFF" opacity="0.98"/>')
            out.append('<text x="18" y="19.8" text-anchor="middle" font-family="Arial,sans-serif" font-size="9.5" font-weight="900" fill="#1971C2">FB</text>')
            out.append('<text x="18" y="27" text-anchor="middle" font-family="Arial,sans-serif" font-size="4.2" font-weight="900" fill="#EC4B91">BINGO</text>')
        out.append(f'<text x="39" y="17" font-family="{font},Arial,sans-serif" font-size="10.5" font-weight="900" fill="#1971C2">FB-<tspan fill="#E94C91">BINGO</tspan></text>')
        if style.show_tagline:
            out.append(f'<text x="39" y="27" font-family="{font},Arial,sans-serif" font-size="5.6" font-weight="800" fill="#1971C2">{escape(style.brand_tagline)}</text>')

        badge_x = width - 86.0
        out.append(f'<rect x="{badge_x:.2f}" y="4" width="28" height="9" rx="3" fill="#EC5A98"/>')
        out.append(f'<text x="{badge_x+14:.2f}" y="10.7" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="5.2" font-weight="900" fill="#FFFFFF">CARTÓN</text>')
        out.append(f'<text x="{width-58:.2f}" y="29" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="23" font-weight="900" fill="#10264A">{card_number}</text>')

        if style.show_qr_zone:
            qr_size = min(40.0, max(34.0, header + 3.0))
            qr_x = width - qr_size - 3.0
            qr_y = 2.0
            out.append(f'<rect class="qr-zone" x="{qr_x:.2f}" y="{qr_y:.2f}" width="{qr_size:.2f}" height="{qr_size:.2f}" rx="1.5" fill="#FFFFFF" stroke="#D7E5EF" stroke-width="0.8"/>')
            q = qr_x + 3.0
            s = qr_size - 6.0
            finder = 9.0
            for fx, fy in ((q, qr_y+3), (q+s-finder, qr_y+3), (q, qr_y+s-finder+3)):
                out.append(f'<rect x="{fx:.2f}" y="{fy:.2f}" width="{finder:.2f}" height="{finder:.2f}" fill="#101820"/>')
                out.append(f'<rect x="{fx+2.1:.2f}" y="{fy+2.1:.2f}" width="4.8" height="4.8" fill="#FFFFFF"/>')
                out.append(f'<rect x="{fx+3.1:.2f}" y="{fy+3.1:.2f}" width="2.8" height="2.8" fill="#101820"/>')
            for dx, dy, ww, hh in ((12,4,5,5),(19,7,4,4),(12,14,4,4),(22,16,3,6),(16,21,5,3),(27,23,4,4),(12,28,5,4),(21,28,3,5),(28,11,4,3)):
                out.append(f'<rect x="{q+dx:.2f}" y="{qr_y+dy:.2f}" width="{ww:.2f}" height="{hh:.2f}" fill="#101820"/>')

        for row in range(3):
            for column in range(9):
                cx = 1.0 + column * (cell_w + gap_x)
                cy = grid_top + row * (cell_h + gap_y)
                value = card.grid[row][column]
                if value is not None:
                    fill = "#FFFFFF"
                elif (row + column) % 2 == 0:
                    fill = "#FCE7EF"
                else:
                    fill = "#EAF6FC"
                out.append(f'<rect x="{cx:.2f}" y="{cy:.2f}" width="{cell_w:.2f}" height="{cell_h:.2f}" rx="2.0" fill="{fill}" stroke="#F08AB1" stroke-width="0.65"/>')
                if value is not None:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.69:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="{number_size:.1f}" font-weight="900" fill="#10264A">{value}</text>')
                elif (row * 2 + column) % 4 == 1:
                    out.append(f'<text x="{cx+cell_w/2:.2f}" y="{cy+cell_h*.70:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="11" font-weight="700" fill="#EE8DB4">☆</text>')

        if style.show_footer:
            fy = height - footer + 0.4
            out.append(f'<rect x="1.5" y="{fy:.2f}" width="{width-3:.2f}" height="{footer-1.2:.2f}" rx="3" fill="#F4FAFE"/>')
            out.append(f'<rect x="4" y="{fy+1.0:.2f}" width="36" height="{max(7.0, footer-3):.2f}" rx="3" fill="#ED4D91"/>')
            out.append(f'<text x="22" y="{height-4.0:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="4.6" font-weight="900" fill="#FFFFFF">SERIE {series}</text>')
            out.append(f'<text x="{width*.50:.2f}" y="{height-4.0:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="4.6" font-weight="900" fill="#23618D">BINGO DE 90 BOLAS</text>')
            out.append(f'<text x="{width-46:.2f}" y="{height-4.0:.2f}" text-anchor="middle" font-family="{font},Arial,sans-serif" font-size="4.6" font-weight="900" fill="#23618D">JUEGA · DIVIÉRTETE · GANA</text>')
        if style.show_serial:
            out.append(f'<text x="{width-2.4:.2f}" y="{height/2:.2f}" text-anchor="middle" font-family="Arial,sans-serif" font-size="3.4" fill="#23618D" transform="rotate(-90 {width-2.4:.2f} {height/2:.2f})">ID: {serial}</text>')
        out.append('</g>')
        return '\n'.join(out)


__all__ = ["ProfessionalA4SvgRenderer"]
