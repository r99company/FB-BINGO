from app.cards import BingoCard, CardModel
from app.printing.layout import A4PrintLayout, PrintStyle


def sample_card(serial: str, model: CardModel = CardModel.A) -> BingoCard:
    return BingoCard(
        serial=serial,
        model=model,
        grid=(
            (1, None, 20, None, 40, None, 60, 70, None),
            (None, 10, None, 30, None, 50, None, None, 80),
            (9, 19, 29, None, 49, None, 69, 79, 90),
        ),
    )


def test_a4_layout_has_six_slots_in_two_columns_and_three_rows():
    layout = A4PrintLayout()
    slots = layout.card_slots()

    assert len(slots) == 6
    assert [slot.index for slot in slots] == [1, 2, 3, 4, 5, 6]
    assert [(slot.column, slot.row) for slot in slots] == [
        (0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2)
    ]

    for slot in slots:
        assert slot.x >= layout.margin
        assert slot.y >= layout.margin
        assert slot.x + slot.width <= layout.page_width - layout.margin
        assert slot.y + slot.height <= layout.page_height - layout.margin


def test_a4_slots_do_not_overlap():
    slots = A4PrintLayout().card_slots()
    for left in slots:
        for right in slots:
            if left.index >= right.index:
                continue
            assert not left.intersects(right)


def test_print_style_has_editable_empty_cell_color_and_logo():
    style = PrintStyle(empty_cell_color="#F7DDE7", logo_path="logo.png")

    assert style.empty_cell_color == "#F7DDE7"
    assert style.logo_path == "logo.png"


def test_layout_assigns_cards_in_series_order():
    cards = tuple(sample_card(f"S1-{i:06d}") for i in range(1, 7))
    placements = A4PrintLayout().place_cards(cards)

    assert [placement.card.serial for placement in placements] == [
        "S1-000001", "S1-000002", "S1-000003",
        "S1-000004", "S1-000005", "S1-000006",
    ]
    assert [placement.slot.index for placement in placements] == [1, 2, 3, 4, 5, 6]
