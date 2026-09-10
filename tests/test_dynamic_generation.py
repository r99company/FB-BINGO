from app.cards import CardModel, SeriesGenerator


def _mask(card):
    return tuple(tuple(cell is not None for cell in row) for row in card.grid)


def test_model_a_allows_three_numbers_in_a_column():
    series = SeriesGenerator(seed=1001).generate("MODEL-A", CardModel.A)
    assert all(1 <= count <= 3 for card in series.cards for count in card.column_counts)


def test_model_b_never_has_three_numbers_in_a_column():
    series = SeriesGenerator(seed=1002).generate("MODEL-B", CardModel.B)
    assert all(1 <= count <= 2 for card in series.cards for count in card.column_counts)


def test_each_series_seeks_strongly_different_card_layouts():
    series = SeriesGenerator(seed=1003).generate("DYNAMIC", CardModel.A)
    masks = [_mask(card) for card in series.cards]
    assert len(set(masks)) >= 4


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
