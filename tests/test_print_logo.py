from pathlib import Path

from app.cards import BingoCard, CardModel
from app.printing import PrintStyle
from app.printing.renderer import render_series_svg


_PIXEL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cf000000020001e221bc330000000049454e44ae426082"
)


def sample_card(serial: str) -> BingoCard:
    return BingoCard(
        serial=serial,
        model=CardModel.A,
        grid=(
            (1, 10, 20, 30, 40, None, None, None, None),
            (9, 19, None, None, None, 50, 60, 70, None),
            (None, None, 29, 39, 49, 59, None, None, 90),
        ),
    )


def test_renderer_embeds_logo_inside_every_card(tmp_path: Path):
    logo = tmp_path / "logo.png"
    logo.write_bytes(_PIXEL_PNG)
    cards = tuple(sample_card(f"S1-{i:06d}") for i in range(1, 7))

    svg = render_series_svg(cards, style=PrintStyle(logo_path=str(logo)))

    assert "data:image/png;base64," in svg
    assert svg.count('class="bingo-card"') == 6
    assert svg.count("data:image/png;base64,") == 6
