from .layout import A4PrintLayout, A4SeriesLayout, CardPlacement, CardSlot, PrintSlot, PrintStyle
from .modern_svg_renderer import ModernA4SvgRenderer

A4SvgRenderer = ModernA4SvgRenderer

__all__ = [
    "A4PrintLayout",
    "A4SeriesLayout",
    "A4SvgRenderer",
    "ModernA4SvgRenderer",
    "CardPlacement",
    "CardSlot",
    "PrintSlot",
    "PrintStyle",
]
