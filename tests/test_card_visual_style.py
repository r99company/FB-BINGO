from app.cards import BingoCard, CardModel
from app.printing.modern_svg_renderer import ModernA4SvgRenderer
from app.printing.layout import PrintStyle


def _card() -> BingoCard:
    return BingoCard(
        serial="0001-11534",
        model=CardModel.A,
        grid=(
            (1, 13, 22, None, 45, None, 67, None, None),
            (5, None, 28, 34, None, 56, None, 78, None),
            (None, 19, None, 39, 48, 59, None, 80, None),
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
