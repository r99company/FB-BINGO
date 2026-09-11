from __future__ import annotations

from app.cards import CardModel
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import ProductionService


def test_next_new_series_start_skips_existing_cards(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    first = service.create_new_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)

    assert service.next_generation_start(6) == 7


def test_new_production_never_reuses_an_existing_range(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    first = service.create_new_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)
    original = repository.get_cards_range(1, 6)

    second = service.create_new_lot(service.next_generation_start(6), 12, CardModel.A, operator="test")
    service.generate_lot(second.lot_id)
    generated = repository.get_cards_range(7, 12)

    assert generated != original
    assert len({service._layout_signature(card) for card in generated}) == 6
    assert {card.serial for card in generated} == {f"0002-{number:06d}" for number in range(7, 13)}


def test_new_production_rejects_a_range_that_already_exists(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)

    first = service.create_new_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(first.lot_id)

    try:
        service.create_new_lot(1, 6, CardModel.A, operator="test")
    except ValueError as exc:
        assert "ya existe" in str(exc).lower()
    else:
        raise AssertionError("Una nueva producción no debe reutilizar un rango existente")


def test_three_consecutive_productions_keep_new_matrices_and_print_data_distinct(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    all_cards = []

    for _ in range(3):
        start = service.next_generation_start(12)
        lot = service.create_new_lot(start, start + 11, CardModel.A, operator="repeat-test")
        service.generate_lot(lot.lot_id)
        all_cards.extend(repository.get_cards_range(start, start + 11))

    signatures = {service._layout_signature(card) for card in all_cards}
    assert len(all_cards) == 36
    assert len(signatures) == 36

    renderer = A4SvgRenderer(style=PrintStyle(show_qr_zone=True))
    first_svg = renderer.render(all_cards[:6])
    second_svg = renderer.render(all_cards[6:12])
    assert first_svg != second_svg
    assert "000001" in first_svg
    assert "000007" in second_svg
