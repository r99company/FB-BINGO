from app.cards import CardModel, SeriesGenerator


def _mask(card):
    return tuple(tuple(cell is not None for cell in row) for row in card.grid)


def _distance(first, second):
    return sum(
        cell_a != cell_b
        for row_a, row_b in zip(first, second)
        for cell_a, cell_b in zip(row_a, row_b)
    )


def test_model_a_all_nine_columns_are_occupied_with_one_or_two_numbers():
    series = SeriesGenerator(seed=1001).generate("MODEL-A", CardModel.A)
    assert all(1 <= count <= 2 for card in series.cards for count in card.column_counts)
    assert all(sum(count == 2 for count in card.column_counts) == 6 for card in series.cards)


def test_model_a_alternates_adjacent_column_masks():
    series = SeriesGenerator(seed=1006).generate("MODEL-A-ROWS", CardModel.A)
    for card in series.cards:
        masks = []
        for column in range(9):
            masks.append(tuple(row for row in range(3) if card.grid[row][column] is not None))
        assert all(left != right for left, right in zip(masks, masks[1:]))


def test_model_b_allows_three_numbers_in_a_column():
    series = SeriesGenerator(seed=1002).generate("MODEL-B", CardModel.B)
    assert all(0 <= count <= 3 for card in series.cards for count in card.column_counts)
    assert all(0 in card.column_counts for card in series.cards)


def test_each_series_has_at_least_five_distinct_card_layouts():
    series = SeriesGenerator(seed=1003).generate("DYNAMIC", CardModel.A)
    masks = [_mask(card) for card in series.cards]
    assert len(set(masks)) >= 5


def test_each_series_avoids_near_duplicate_card_layouts():
    series = SeriesGenerator(seed=1005).generate("DYNAMIC-DISTANCE", CardModel.A)
    masks = [_mask(card) for card in series.cards]
    distances = [_distance(masks[i], masks[j]) for i in range(6) for j in range(i + 1, 6)]
    assert min(distances) >= 8


def test_250_series_can_be_generated_without_random_failure():
    generator = SeriesGenerator(seed=1004)
    for series_number in range(1, 251):
        series = generator.generate(
            f"{series_number:04d}",
            CardModel.A,
            serial_start=(series_number - 1) * 6 + 1,
        )
        assert len(series.cards) == 6
        assert sorted(n for card in series.cards for n in card.numbers) == list(range(1, 91))
