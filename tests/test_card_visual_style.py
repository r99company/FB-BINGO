from app.cards import BingoCard, CardModel
from app.printing.modern_svg_renderer import ModernA4SvgRenderer
from app.printing.layout import PrintStyle


def _card() -> BingoCard:
    return BingoCard(
        serial="0001-11534",
        model=CardModel.A,
        grid=(
            (9, None, 15, None, 33, 45, 55, None, None),
            (6, None, 20, 31, 49, 60, None, None, None),
            (1, 10, 22, 32, None, None, None, None, None),
        ),
    )


def test_card_renderer_has_fb_bingo_visual_language():
    renderer = ModernA4SvgRenderer(style=PrintStyle(show_model=False, show_serial=True, show_qr_zone=True))
    svg = renderer.render([_card()] * 6)

    assert '<circle' in svg
    assert 'FB-BINGO' in svg
    assert '#FF4FA3' in svg
    assert '#8FD9FF' in svg
    assert '★' in svg
    assert 'CARTÓN' in svg
    assert 'SERIE 0001' in svg
