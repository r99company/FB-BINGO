from app.cards import CardModel, SeriesGenerator
from app.printing import A4SvgRenderer


def _card(model: CardModel):
    return SeriesGenerator(seed=41).generate("001", model, 1).cards[0]


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
