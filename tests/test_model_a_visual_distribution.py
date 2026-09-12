from __future__ import annotations

from app.cards import CardModel, SeriesGenerator
from app.cards.distribution import COLUMNS, DistributionModel


def _column_mask(card, column: int) -> int:
    mask = 0
    for row in range(3):
        if card.grid[row][column] is not None:
            mask |= 1 << row
    return mask


def test_model_a_never_forms_three_consecutive_numbers_in_a_row() -> None:
    for seed in range(30):
        series = SeriesGenerator(seed=seed).generate(f"VIS-{seed:03d}", CardModel.A)
        for card in series.cards:
            for row in card.grid:
                occupied = [value is not None for value in row]
                run = longest = 0
                for present in occupied:
                    run = run + 1 if present else 0
                    longest = max(longest, run)
                assert longest <= 2


def test_model_a_changes_row_positions_between_adjacent_columns() -> None:
    for seed in range(30):
        series = SeriesGenerator(seed=seed).generate(f"ALT-{seed:03d}", CardModel.A)
        for card in series.cards:
            masks = [_column_mask(card, column) for column in range(COLUMNS)]
            assert all(left != right for left, right in zip(masks, masks[1:]))


def test_model_a_balances_left_middle_and_right_zones() -> None:
    model = DistributionModel.for_model(CardModel.A)
    for seed in range(30):
        series = SeriesGenerator(seed=seed).generate(f"ZONE-{seed:03d}", CardModel.A)
        for card in series.cards:
            zones = [
                sum(value is not None for row in card.grid for value in row[zone_start:zone_start + 3])
                for zone_start in (0, 3, 6)
            ]
            assert max(zones) - min(zones) <= 2
