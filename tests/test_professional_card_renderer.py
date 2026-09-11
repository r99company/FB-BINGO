from app.cards import BingoCard, CardModel
from app.printing import A4SvgRenderer


def _card(model: CardModel) -> BingoCard:
    grid = (
        (1, None, 23, None, 45, 56, None, 78, None),
        (None, 12, None, 34, None, 67, 79, None, 89),
        (9, 19, 29, None, 49, None, None, None, 90),
    )
    return BingoCard("001-00001", model, grid)


def test_professional_renderer_keeps_approved_card_composition_for_model_a():
    svg = A4SvgRenderer().render_card(_card(CardModel.A))
    assert "CARTÓN" in svg
    assert "FB-" in svg and "BINGO" in svg
    assert "BINGO DE 90 BOLAS" in svg
    assert "JUEGA · DIVIÉRTETE · GANA" in svg
    assert "☆" in svg
    assert 'stroke="#D7E5EF"' in svg
    assert 'font-size="23"' in svg


def test_professional_renderer_uses_same_visual_template_for_model_b():
    svg = A4SvgRenderer().render_card(_card(CardModel.B))
    assert "CARTÓN" in svg
    assert "BINGO DE 90 BOLAS" in svg
    assert 'stroke="#F08AB1"' in svg
