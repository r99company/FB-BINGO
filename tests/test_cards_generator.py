from app.cards import CardModel, SeriesGenerator


def test_model_a_first_four_columns_use_all_three_rows():
    for seed in range(30):
        series = SeriesGenerator(seed=seed).generate(f"PREFIX-{seed:03d}", CardModel.A)
        for card in series.cards:
            counts = [
                sum(card.grid[row][column] is not None for column in range(4))
                for row in range(3)
            ]
            assert all(count >= 1 for count in counts)
