from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer
from app.production import ProductionService


def test_model_b_series_has_six_cards_and_covers_1_to_90():
    series = SeriesGenerator(seed=20260908).generate("0100", CardModel.B, serial_start=595)

    assert len(series.cards) == 6
    assert sorted(n for card in series.cards for n in card.numbers) == list(range(1, 91))
    for card in series.cards:
        assert max(card.column_counts) <= 3
        assert all(sum(value is not None for value in row) == 5 for row in card.grid)


def test_multiple_series_roundtrip_keeps_serial_to_series_position(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, max_cards=30_000)
    lot = service.create_lot(7, 18, CardModel.A, operator="test")
    service.generate_lot(lot.lot_id)

    assert repository.count_series() == 2
    assert repository.count_cards() == 12

    for serial, expected_series, expected_position in (
        ("000007", "0002", 1),
        ("000012", "0002", 6),
        ("000013", "0003", 1),
        ("000018", "0003", 6),
    ):
        card = repository.get_card(serial)
        assert repository.get_series_id_for_card(card.serial) == expected_series
        assert repository.get_card_position(card.serial) == (expected_series, expected_position)


def test_a4_renderer_keeps_each_series_as_six_cards(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, max_cards=30_000)
    lot = service.create_lot(1, 12, CardModel.A, operator="test")
    service.generate_lot(lot.lot_id)

    first = repository.get("0001")
    second = repository.get("0002")
    svg = A4SvgRenderer().render(first.cards)

    assert svg.count('class="bingo-card"') == 6
    assert all(card.serial in svg for card in first.cards)
    assert not any(card.serial in svg for card in second.cards)
