import pytest

from app.cards import BingoCard, CardModel
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


def test_card_accepts_columns_with_one_two_or_three_numbers() -> None:
    grid = (
        (1, 11, 21, None, 41, None, 61, None, 81),
        (2, None, 22, 32, None, 52, None, 72, None),
        (3, None, None, 39, None, 59, 69, None, 89),
    )

    card = BingoCard(serial="B-000001", model=CardModel.B, grid=grid)

    assert card.column_counts == (3, 1, 2, 2, 1, 2, 1, 1, 2)
    assert sum(card.column_counts) == 15


def test_verification_uses_actual_row_positions_not_model_name() -> None:
    grid = (
        (1, None, 21, None, 41, None, 61, None, 81),
        (None, 12, None, 32, 44, 52, None, 72, None),
        (9, None, 29, 39, None, 59, None, None, 89),
    )
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
