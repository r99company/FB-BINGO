from app.cards import CardModel, SeriesGenerator


def test_series_has_six_cards_and_ninety_unique_numbers() -> None:
    series = SeriesGenerator(seed=123).generate("SER-001", CardModel.A, serial_start=1)
    assert len(series.cards) == 6
    numbers = [n for card in series.cards for n in card.numbers]
    assert len(numbers) == 90
    assert sorted(numbers) == list(range(1, 91))


def test_model_a_cards_have_five_numbers_per_row_and_one_or_two_per_column() -> None:
    series = SeriesGenerator(seed=456).generate("SER-A", CardModel.A)
    for card in series.cards:
        assert [sum(cell is not None for cell in row) for row in card.grid] == [5, 5, 5]
        assert all(1 <= count <= 2 for count in card.column_counts)


def test_column_positions_are_not_one_fixed_mask_repeated_six_times() -> None:
    series = SeriesGenerator(seed=789).generate("SER-MASK", CardModel.A)
    masks = {
        tuple(tuple(cell is not None for cell in row) for row in card.grid)
        for card in series.cards
    }
    assert len(masks) >= 2


def test_numbers_stay_in_their_bingo_column_ranges() -> None:
    ranges = [(1, 9), *[(10 * i, 10 * i + 9) for i in range(1, 8)], (80, 90)]
    series = SeriesGenerator(seed=321).generate("SER-RANGES", CardModel.A)
    for card in series.cards:
        for column, (low, high) in enumerate(ranges):
            for row in range(3):
                value = card.grid[row][column]
                if value is not None:
                    assert low <= value <= high


def test_multiple_series_remain_valid() -> None:
    generator = SeriesGenerator(seed=999)
    for series_id in range(1, 21):
        series = generator.generate(str(series_id), CardModel.A, serial_start=1 + (series_id - 1) * 6)
        numbers = [n for card in series.cards for n in card.numbers]
        assert len(numbers) == 90
        assert sorted(numbers) == list(range(1, 91))
