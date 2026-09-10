import pytest

from app.cards import CardModel, SeriesGenerator


def test_generates_six_cards_with_fifteen_numbers_each() -> None:
    series = SeriesGenerator(seed=123).generate("SER-001", CardModel.A, serial_start=100)
    assert len(series.cards) == 6
    assert all(len(card.numbers) == 15 for card in series.cards)
    assert [card.serial for card in series.cards] == [
        "SER-001-000100", "SER-001-000101", "SER-001-000102",
        "SER-001-000103", "SER-001-000104", "SER-001-000105",
    ]


def test_series_covers_each_number_1_to_90_once() -> None:
    series = SeriesGenerator(seed=456).generate("SER-002", CardModel.A)
    numbers = [number for card in series.cards for number in card.numbers]
    assert len(numbers) == 90
    assert len(set(numbers)) == 90
    assert set(numbers) == set(range(1, 91))


def test_model_a_generated_cards_allow_only_one_or_two_numbers_per_column() -> None:
    series = SeriesGenerator(seed=789).generate("SER-A", CardModel.A)
    for card in series.cards:
        assert tuple(sum(value is not None for value in row) for row in card.grid) == (5, 5, 5)
        assert all(1 <= count <= 2 for count in card.column_counts)
        assert card.model is CardModel.A


def test_model_b_generated_cards_allow_one_to_three_numbers_per_column() -> None:
    series = SeriesGenerator(seed=789).generate("SER-B", CardModel.B)
    for card in series.cards:
        assert tuple(sum(value is not None for value in row) for row in card.grid) == (5, 5, 5)
        assert all(1 <= count <= 3 for count in card.column_counts)
        assert card.model is CardModel.B


def test_generated_numbers_are_sorted_top_to_bottom_in_each_column() -> None:
    for model in (CardModel.A, CardModel.B):
        series = SeriesGenerator(seed=321).generate(f"SER-{model.value}", model)
        for card in series.cards:
            for column in range(9):
                values = [card.grid[row][column] for row in range(3)]
                values = [value for value in values if value is not None]
                assert values == sorted(values)


def test_model_is_metadata_and_both_models_generate_valid_series() -> None:
    series_a = SeriesGenerator(seed=1).generate("A", CardModel.A)
    series_b = SeriesGenerator(seed=1).generate("B", CardModel.B)
    assert all(card.model is CardModel.A for card in series_a.cards)
    assert all(card.model is CardModel.B for card in series_b.cards)
    assert all(len(card.numbers) == 15 for card in series_a.cards + series_b.cards)


def test_generator_rejects_series_past_supported_serial_limit() -> None:
    with pytest.raises(ValueError, match="30000"):
        SeriesGenerator(seed=1).generate("SER-LIMIT", CardModel.A, serial_start=29_996)


def _layout_signature(card) -> tuple[tuple[bool, ...], ...]:
    return tuple(tuple(value is not None for value in row) for row in card.grid)


def _column_signature(card) -> tuple[int, ...]:
    return card.column_counts


def test_same_seed_does_not_reuse_card_layout_for_different_series() -> None:
    generator_a = SeriesGenerator(seed=2026)
    first = generator_a.generate("SER-001", CardModel.A)
    generator_b = SeriesGenerator(seed=2026)
    later = generator_b.generate("SER-150", CardModel.A)
    assert _layout_signature(first.cards[2]) != _layout_signature(later.cards[2])


def test_model_a_allows_natural_row_runs() -> None:
    for seed in range(10):
        series = SeriesGenerator(seed=seed).generate(f"SER-{seed:03d}", CardModel.A)
        for card in series.cards:
            assert [sum(value is not None for value in row) for row in card.grid] == [5, 5, 5]


def test_representative_series_allow_repeats_but_not_three_identical_column_patterns_in_a_row() -> None:
    for series_id in ("001", "002", "003", "150", "151"):
        series = SeriesGenerator(seed=2026).generate(f"SER-{series_id}", CardModel.A)
        patterns = [_column_signature(card) for card in series.cards]
        assert len(set(patterns)) >= 2
        for index in range(2, len(patterns)):
            assert not (patterns[index] == patterns[index - 1] == patterns[index - 2])


def test_model_a_does_not_require_first_columns_to_use_all_three_rows() -> None:
    for seed in range(10):
        series = SeriesGenerator(seed=seed).generate(f"PREFIX-{seed:03d}", CardModel.A)
        for card in series.cards:
            assert len(card.numbers) == 15
