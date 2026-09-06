from app.cards import CardModel, SeriesGenerator


def _mask(card):
    return tuple(tuple(value is not None for value in row) for row in card.grid)


def test_series_has_more_than_one_card_mask_pattern():
    series = SeriesGenerator(seed=20260905).generate("MASK-001", CardModel.A)
    masks = {_mask(card) for card in series.cards}
    assert len(masks) >= 2


def test_different_seeds_can_produce_different_mask_sets():
    first = SeriesGenerator(seed=11).generate("MASK-A", CardModel.A)
    second = SeriesGenerator(seed=12).generate("MASK-B", CardModel.A)
    first_masks = tuple(_mask(card) for card in first.cards)
    second_masks = tuple(_mask(card) for card in second.cards)
    assert first_masks != second_masks


def test_distribution_model_is_explicit_generation_boundary():
    from app.cards.distribution import DistributionModel

    assert DistributionModel.for_model(CardModel.A).model is CardModel.A
    assert DistributionModel.for_model(CardModel.B).model is CardModel.B
