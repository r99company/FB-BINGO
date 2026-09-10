from app.printing.batches import iter_a4_series_batches


def test_1500_cards_are_250_series_and_125_a4_pages_without_duplication():
    batches = list(iter_a4_series_batches(1, 250, duplicate=False))

    assert len(batches) == 125
    assert batches[0] == (1, 2)
    assert batches[-1] == (249, 250)


def test_duplicate_print_repeats_each_series_on_both_columns():
    batches = list(iter_a4_series_batches(1, 3, duplicate=True))

    assert batches == [(1, 1), (2, 2), (3, 3)]


def test_non_duplicate_print_leaves_last_series_alone_when_series_count_is_odd():
    batches = list(iter_a4_series_batches(10, 3, duplicate=False))

    assert batches == [(10, 11), (12, None)]
