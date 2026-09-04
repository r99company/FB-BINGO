from app.cards import CardModel, SeriesGenerator
from app.printing import A4SeriesLayout


def test_a4_layout_places_six_cards_in_two_columns() -> None:
    series = SeriesGenerator(seed=123).generate("SER-001", CardModel.A)

    layout = A4SeriesLayout.for_series(series)

    assert layout.page_size == "A4"
    assert layout.columns == 2
    assert layout.cards_per_page == 6
    assert [slot.card.serial for slot in layout.slots] == [card.serial for card in series.cards]
    assert [(slot.row, slot.column) for slot in layout.slots] == [
        (0, 0), (0, 1), (1, 0), (1, 1), (2, 0), (2, 1)
    ]


def test_layout_keeps_model_and_exact_grid_for_printing() -> None:
    series = SeriesGenerator(seed=456).generate("SER-002", CardModel.B)

    layout = A4SeriesLayout.for_series(series)

    for slot, card in zip(layout.slots, series.cards):
        assert slot.card.model is CardModel.B
        assert slot.card.grid == card.grid
        assert slot.serial == card.serial
