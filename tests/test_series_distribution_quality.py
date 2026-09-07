from app.cards import CardModel, SeriesGenerator


def _mask(card):
    return tuple(tuple(cell is not None for cell in row) for row in card.grid)


def test_model_a_series_has_six_distinct_card_masks_and_exact_column_loads() -> None:
    series = SeriesGenerator(seed=20260906).generate("DIST-001", CardModel.A, serial_start=1)
    masks = [_mask(card) for card in series.cards]
    assert len(set(masks)) == 6
    loads = [
        sum(card.grid[row][column] is not None for card in series.cards for row in range(3))
        for column in range(9)
    ]
    assert loads == [9, 10, 10, 10, 10, 10, 10, 10, 11]


def test_model_a_each_card_keeps_five_numbers_per_row_and_15_total() -> None:
    series = SeriesGenerator(seed=20260907).generate("DIST-002", CardModel.A, serial_start=7)
    for card in series.cards:
        assert [sum(value is not None for value in row) for row in card.grid] == [5, 5, 5]
        assert len(card.numbers) == 15
