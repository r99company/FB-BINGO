import pytest

from app.game.session import BingoSession


def test_start_and_call_tracks_last_five():
    session = BingoSession()
    session.start()
    for number in range(1, 7):
        session.call(number)
    assert session.called_numbers == [1, 2, 3, 4, 5, 6]
    assert session.last_five == (2, 3, 4, 5, 6)


def test_rejects_invalid_and_duplicate_balls():
    session = BingoSession()
    session.start()
    session.call(90)
    with pytest.raises(ValueError): session.call(91)
    with pytest.raises(ValueError): session.call(90)


def test_winner_requires_all_numbers_to_have_been_called():
    session = BingoSession()
    session.start(); session.call(10); session.call(20)
    assert session.is_winner([10, 20]) is True
    assert session.is_winner([10, 20, 30]) is False
