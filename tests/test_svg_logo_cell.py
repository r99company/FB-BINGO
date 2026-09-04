from pathlib import Path

from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer, PrintStyle


_PIXEL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c489"
    "0000000d49444154789c6360f8cf000000020001e221bc330000000049454e44ae426082"
)


def test_a4_renderer_places_logo_in_an_empty_cell_of_each_card(tmp_path: Path):
    logo = tmp_path / "logo.png"
    logo.write_bytes(_PIXEL_PNG)
    card = BingoCard(
        serial="1-000001",
        model=CardModel.A,
        grid=((1, 10, None, 30, None, None, None, None, None),
              (9, None, 20, None, 40, 50, None, None, None),
              (None, 19, None, None, None, None, 70, 80, 90)),
    )
    svg = A4SvgRenderer(style=PrintStyle(logo_path=str(logo))).render(tuple(card for _ in range(6)))

    assert svg.count("data:image/png;base64,") == 6
    assert svg.count("preserveAspectRatio=\"xMidYMid meet\"") == 6
