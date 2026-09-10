from app.cards import CardModel, SeriesGenerator


def test_model_a_avoids_three_consecutive_numbers_in_a_row():
    for seed in range(30):
        series = SeriesGenerator(seed=seed).generate(f"INTERLEAVE-{seed:03d}", CardModel.A)
        for card in series.cards:
            for row in card.grid:
                longest = 0
                current = 0
                for value in row:
                    current = current + 1 if value is not None else 0
                    longest = max(longest, current)
                assert longest <= 2
