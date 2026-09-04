from app.cards import BingoCard, CardModel
from app.verification.check import CardCheckService


def make_card() -> BingoCard:
    return BingoCard(
        serial="000001",
        model=CardModel.B,
        grid=(
            (1, 10, 20, 30, 40, None, None, None, None),
            (9, 19, None, None, None, 50, 60, 70, None),
            (None, None, 29, 39, 49, 59, None, None, 90),
        ),
    )


def test_check_uses_exact_matrix_and_reports_line():
    result = CardCheckService.check(make_card(), {1, 10, 20, 30, 40})
    assert result.serial == "000001"
    assert result.model == "B"
    assert result.line_rows == (0,)
    assert not result.bingo
    assert result.has_prize


def test_check_reports_bingo_only_when_all_numbers_are_called():
    card = make_card()
    called = set(card.numbers)
    result = CardCheckService.check(card, called)
    assert result.bingo
    assert result.line_rows == (0, 1, 2)


def test_check_rejects_invalid_ball():
    try:
        CardCheckService.check(make_card(), {1, 91})
    except ValueError as exc:
        assert "1 y 90" in str(exc)
    else:
        raise AssertionError("Expected ValueError")
