from app.cards import BingoCard, CardModel
from app.printing.layout import A4PrintLayout, PrintStyle


def sample_card(serial: str, model: CardModel = CardModel.A) -> BingoCard:
    return BingoCard(
        serial=serial,
        model=model,
        grid=(
            (1, 10, 20, 30, 40, None, None, None, None),
            (9, 19, None, None, None, 50, 60, 70, None),
            (None, None, 29, 39, 49, 59, None, None, 90),
        ),
    )


def test_a4_layout_has_twelve_slots_in_two_columns_and_six_rows():
    layout = A4PrintLayout()
    slots = layout.card_slots()
    assert len(slots) == 12
    assert [slot.index for slot in slots] == list(range(1, 13))
    assert [(slot.column, slot.row) for slot in slots] == [
        (0, 0), (1, 0), (0, 1), (1, 1), (0, 2), (1, 2),
        (0, 3), (1, 3), (0, 4), (1, 4), (0, 5), (1, 5),
    ]
    for slot in slots:
        assert slot.x >= layout.margin
        assert slot.y >= layout.margin
        assert slot.x + slot.width <= layout.page_width - layout.margin
        assert slot.y + slot.height <= layout.page_height - layout.margin


def test_default_a4_card_size_is_95x44_mm_for_two_series_per_page():
    layout = A4PrintLayout()
    slots = layout.card_slots()
    assert layout.card_width_mm == 95.0
    assert layout.card_height_mm == 44.0
    assert abs(slots[0].width / layout.MM_TO_PT - 95.0) < 0.01
    assert abs(slots[0].height / layout.MM_TO_PT - 44.0) < 0.01
    assert abs((slots[1].x - slots[0].x - slots[0].width) / layout.MM_TO_PT - 3.0) < 0.01
    assert abs((slots[2].y - slots[0].y - slots[0].height) / layout.MM_TO_PT - 2.5) < 0.01


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
    assert [placement.card.serial for placement in placements] == [f"S1-{i:06d}" for i in range(1, 7)]
    assert [placement.slot.index for placement in placements] == [1, 2, 3, 4, 5, 6]


def test_layout_can_duplicate_left_column_for_troquelado():
    cards = tuple(sample_card(f"S1-{i:06d}") for i in range(1, 7))
    placements = A4PrintLayout().place_columns(cards, cards)
    # Physical reading order is row-by-row: each row contains the same
    # card on the left and right when duplicating the column for troquelado.
    assert [placement.card.serial for placement in placements] == [
        serial for i in range(1, 7) for serial in (f"S1-{i:06d}", f"S1-{i:06d}")
    ]
    assert [placement.slot.index for placement in placements] == list(range(1, 13))
