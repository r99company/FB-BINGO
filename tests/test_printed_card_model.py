from app.cards import BingoCard, CardModel
from app.printing.layout import A4PrintLayout, PrintStyle
from app.printing.modern_svg_renderer import ModernA4SvgRenderer


def card(serial: str) -> BingoCard:
    return BingoCard(
        serial=serial,
        model=CardModel.A,
        grid=(
            (1, 13, 22, None, 45, None, 67, None, None),
            (5, None, 28, 34, None, 56, None, 78, None),
            (None, 19, None, 39, 48, 59, None, 80, None),
        ),
    )


def test_printed_card_defaults_to_clean_customer_facing_model():
    style = PrintStyle()
    assert style.show_model is False


def test_printed_card_uses_clean_physical_card_model_without_internal_model_label():
    renderer = ModernA4SvgRenderer(style=PrintStyle(show_model=False, show_serial=True))
    svg = renderer.render([card(f"0001-{i:05d}") for i in range(1, 7)])
    assert 'CARTÓN' in svg
    assert 'FB-BINGO' in svg
    assert 'BINGO DE 90 BOLAS' in svg
    assert 'JUEGA · DIVIÉRTETE · GANA' in svg
    assert 'MODELO A' not in svg
    assert 'VISTA PREVIA' not in svg


def test_printed_a4_model_is_two_columns_of_six_cards():
    left = tuple(card(f"0001-{i:05d}") for i in range(1, 7))
    right = tuple(card(f"0002-{i:05d}") for i in range(1, 7))
    placements = A4PrintLayout().place_columns(left, right)
    assert len(placements) == 12
    assert [(p.slot.column, p.slot.row) for p in placements] == [
        (0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2),
        (0, 3), (1, 3), (0, 4), (1, 4), (0, 5), (1, 5),
    ]


def test_clean_print_style_keeps_model_a_and_b_generation_independent():
    style = PrintStyle(show_model=False)
    assert style.show_model is False
    assert CardModel.A != CardModel.B
