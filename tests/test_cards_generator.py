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


def test_each_generated_card_has_valid_rows_and_columns() -> None:
    for model in (CardModel.A, CardModel.B):
        series = SeriesGenerator(seed=789).generate(f"SER-{model.value}", model)
        for card in series.cards:
            assert tuple(sum(value is not None for value in row) for row in card.grid) == (5, 5, 5)
            assert all(1 <= count <= 3 for count in card.column_counts)
            assert card.model is model


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


def test_generate_batch_creates_consecutive_series_and_serials() -> None:
    series = list(
        SeriesGenerator(seed=42).generate_batch(
            series_start=10,
            quantity=3,
            model=CardModel.A,
            serial_start=1,
        )
    )

    assert [item.series_id for item in series] == ["10", "11", "12"]
    assert [card.serial for item in series for card in item.cards] == [
        f"{series_id}-{serial:06d}"
        for series_id, serial in zip(("10", "11", "12"), range(1, 19))
    ]


def test_generate_batch_rejects_invalid_quantity_and_serial_range() -> None:
    generator = SeriesGenerator(seed=1)

    with pytest.raises(ValueError, match="quantity"):
        list(generator.generate_batch(1, 0, CardModel.A, 1))

    with pytest.raises(ValueError, match="30000"):
        list(generator.generate_batch(1, 2_500, CardModel.A, 15_001))
