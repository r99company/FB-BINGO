import pytest

from app.cards import BingoCard, CardModel, SeriesGenerator
from app.verification import CardVerifier


def sample_matrix() -> tuple[tuple[int | None, ...], ...]:
    return (
        (1, None, 21, None, 41, None, 61, None, 81),
        (None, 12, None, 32, 44, 52, None, 72, None),
        (9, None, 29, 39, None, 59, None, None, 89),
    )


def test_card_keeps_model_and_exact_positions() -> None:
    card = BingoCard(serial="A-000001", model=CardModel.A, grid=sample_matrix())

    assert card.model is CardModel.A
    assert card.serial == "A-000001"
    assert card.numbers == frozenset({1, 9, 12, 21, 29, 32, 39, 41, 44, 52, 59, 61, 72, 81, 89})
    assert card.row_numbers(0) == (1, 21, 41, 61, 81)


def test_model_a_accepts_one_or_two_numbers_per_column() -> None:
    card = BingoCard(serial="A-000002", model=CardModel.A, grid=sample_matrix())
    assert all(count in (1, 2) for count in card.column_counts)


def test_model_a_rejects_three_numbers_in_a_column() -> None:
    grid = (
        (1, 11, 21, None, 41, None, None, None, 81),
        (2, None, 22, 32, None, 52, None, 72, None),
        (3, None, None, 39, None, 59, 69, None, 89),
    )

    with pytest.raises(ValueError, match="entre 1 y 2"):
        BingoCard(serial="A-000003", model=CardModel.A, grid=grid)


def test_model_b_accepts_one_two_or_three_numbers_per_column() -> None:
    grid = (
        (1, 11, 21, None, 41, None, None, None, 81),
        (2, None, 22, 32, None, 52, None, 72, None),
        (3, None, None, 39, None, 59, 69, None, 89),
    )

    card = BingoCard(serial="B-000001", model=CardModel.B, grid=grid)

    assert card.column_counts == (3, 1, 2, 2, 1, 2, 1, 1, 2)
    assert sum(card.column_counts) == 15


def test_model_a_generates_valid_series_with_varied_masks() -> None:
    generator = SeriesGenerator(seed=20260905)
    signatures: set[tuple[tuple[int, ...], ...]] = set()

    for series_number in range(1, 31):
        series = generator.generate(str(series_number), CardModel.A, (series_number - 1) * 6 + 1)
        assert len(series.cards) == 6
        assert all(card.model is CardModel.A for card in series.cards)
        assert all(all(count in (1, 2) for count in card.column_counts) for card in series.cards)
        assert set().union(*(card.numbers for card in series.cards)) == set(range(1, 91))
        assert sum(len(card.numbers) for card in series.cards) == 90

        for card in series.cards:
            mask = tuple(
                tuple(column for column in range(9) if card.grid[row][column] is not None)
                for row in range(3)
            )
            signatures.add(mask)

    assert len(signatures) >= 10


def test_verification_uses_actual_row_positions_not_model_name() -> None:
    grid = sample_matrix()
    called = {1, 21, 41, 61, 81}

    card_a = BingoCard(serial="A-1", model=CardModel.A, grid=grid)
    card_b = BingoCard(serial="B-1", model=CardModel.B, grid=grid)

    assert CardVerifier(card_a).line_winners(called) == (0,)
    assert CardVerifier(card_b).line_winners(called) == (0,)
    assert not CardVerifier(card_a).is_bingo(called)
    assert not CardVerifier(card_b).is_bingo(called)


def test_bingo_requires_all_numbers_of_that_exact_card() -> None:
    card = BingoCard(serial="A-2", model=CardModel.A, grid=sample_matrix())
    verifier = CardVerifier(card)

    assert not verifier.is_bingo(set(card.numbers) - {89})
    assert verifier.is_bingo(card.numbers)


def test_invalid_card_is_rejected() -> None:
    invalid = (
        (1, None, 21, None, 41, None, 61, None, 91),
        (None, 12, None, 32, 44, 52, None, 72, None),
        (9, None, 29, 39, None, 59, None, None, 89),
    )

    with pytest.raises(ValueError):
        BingoCard(serial="A-3", model=CardModel.A, grid=invalid)
