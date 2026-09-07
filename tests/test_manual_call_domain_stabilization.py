from app.bingo import BingoGame

def test_manual_call_domain_placeholder():
    assert hasattr(BingoGame, 'call_manual')
