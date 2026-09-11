from __future__ import annotations

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import ProductionService


def test_next_new_series_start_skips_existing_cards(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)
    assert service.next_generation_start(6) == 7


def test_same_range_generation_is_idempotent(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)
    original = [card.grid for card in repository.get_cards_range(1, 6)]

    again = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(again.lot_id)
    repeated = [card.grid for card in repository.get_cards_range(1, 6)]

    assert original == repeated


def test_next_block_has_different_matrices(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    first = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)
    second = service.create_lot(7, 12, CardModel.A, operator="test")
    service.generate_lot(second.lot_id)

    first_grids = [card.grid for card in repository.get_cards_range(1, 6)]
    second_grids = [card.grid for card in repository.get_cards_range(7, 12)]
    assert first_grids != second_grids
    assert {card.serial for card in repository.get_cards_range(7, 12)} == {f"0002-{number:06d}" for number in range(7, 13)}


def test_three_consecutive_productions_keep_new_matrices_and_print_data_distinct(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    all_cards = []
    for _ in range(3):
        start = service.next_generation_start(12)
        lot = service.create_lot(start, start + 11, CardModel.A, operator="repeat-test")
        service.generate_lot(lot.lot_id)
        all_cards.extend(repository.get_cards_range(start, start + 11))

    signatures = {service._layout_signature(card) for card in all_cards}
    assert len(all_cards) == 36
    assert len(signatures) == 36
    renderer = A4SvgRenderer(style=PrintStyle(show_qr_zone=True))
    assert renderer.render(all_cards[:6]) != renderer.render(all_cards[6:12])


def test_series_generator_is_stable_for_same_series():
    generator = SeriesGenerator(seed=123)
    first = generator.generate("0001", CardModel.A, 1)
    second = generator.generate("0001", CardModel.A, 1)
    assert [card.grid for card in first.cards] == [card.grid for card in second.cards]


def test_series_generator_changes_with_series_id():
    generator = SeriesGenerator(seed=123)
    first = generator.generate("0001", CardModel.A, 1)
    second = generator.generate("0002", CardModel.A, 7)
    assert [card.grid for card in first.cards] != [card.grid for card in second.cards]
