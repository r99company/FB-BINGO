from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer, PrintStyle


def card() -> BingoCard:
    return BingoCard(
        serial="S1-000001",
        model=CardModel.B,
        grid=(
            (1, None, 20, None, 40, None, 60, None, 80),
            (None, 10, None, 30, None, 50, None, 70, None),
            (9, 19, 29, 39, 49, 59, 69, 79, 90),
        ),
    )


def test_renderer_contains_serial_model_and_all_numbers():
    cards = tuple(card().with_serial(f"S1-{i:06d}") if hasattr(card(), "with_serial") else card() for i in range(1, 7))
    svg = A4SvgRenderer(style=PrintStyle(empty_cell_color="#ABCDEF")).render(cards)

    assert svg.startswith("<svg ")
    assert "210mm" in svg
    assert "297mm" in svg
    assert "MODELO B" in svg
    assert "S1-000001" in svg
    assert "#ABCDEF" in svg
    for number in (1, 10, 20, 30, 40, 50, 60, 70, 80, 90):
        assert f">{number}</text>" in svg
