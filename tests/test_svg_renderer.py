from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer, PrintStyle


def card(serial: str) -> BingoCard:
    return BingoCard(
        serial=serial,
        model=CardModel.B,
        grid=(
            (1, 10, 20, 30, 40, None, None, None, None),
            (9, 19, None, None, None, 50, 60, 70, None),
            (None, None, 29, 39, 49, 59, None, None, 90),
        ),
    )


def test_renderer_contains_serial_model_and_all_numbers():
    cards = tuple(card(f"S1-{i:06d}") for i in range(1, 7))
    svg = A4SvgRenderer(style=PrintStyle(empty_cell_color="#ABCDEF")).render(cards)
    assert svg.startswith("<svg ")
    assert "210mm" in svg
    assert "297mm" in svg
    assert "MODELO B" in svg
    assert "S1-000001" in svg
    assert "S1-000006" in svg
    assert "#ABCDEF" in svg
    for number in (1, 10, 20, 30, 40, 50, 60, 70, 80, 90):
        assert f">{number}</text>" in svg
