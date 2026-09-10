from app.cards import CardModel, SeriesGenerator


def test_model_a_varies_column_counts_without_forcing_a_fixed_pattern():
    for seed in range(30):
        series = SeriesGenerator(seed=seed).generate(f"INTERLEAVE-{seed:03d}", CardModel.A)
        patterns = [card.column_counts for card in series.cards]
        assert len(set(patterns)) >= 2
        for index in range(2, len(patterns)):
            assert not (patterns[index] == patterns[index - 1] == patterns[index - 2])
