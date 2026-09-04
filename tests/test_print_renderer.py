from app.cards import BingoCard, CardModel
from app.printing.layout import A4PrintLayout, PrintStyle
from app.printing.renderer import render_series_svg


def card(serial: str) -> BingoCard:
    return BingoCard(
        serial=serial,
        model=CardModel.B,
        grid=(
            (1, None, 20, None, 40, None, 60, 70, None),
            (None, 10, None, 30, None, 50, None, None, 80),
            (9, 19, 29, None, 49, None, 69, 79, 90),
        ),
    )


def test_render_series_svg_contains_six_cards_serials_model_and_style():
    cards = tuple(card(f"S7-{i:06d}") for i in range(1, 7))
    svg = render_series_svg(cards, PrintStyle(empty_cell_color="#123456"))

    assert svg.startswith("<svg ")
    assert svg.count('class="bingo-card"') == 6
    assert "S7-000001" in svg
    assert "S7-000006" in svg
    assert "MODELO B" in svg
    assert "#123456" in svg
    assert 'width="595.2756pt"' in svg
    assert 'height="841.8898pt"' in svg
