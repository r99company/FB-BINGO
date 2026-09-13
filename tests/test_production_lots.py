import pytest

from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.production import DuplicateProductionError, ProductionService, plan_lot


def test_1500_cards_make_250_series() -> None:
    lot = plan_lot(1, 1500)
    assert lot.card_count == 1500
    assert lot.series_count == 250


def test_lot_can_start_at_any_card_when_quantity_is_six() -> None:
    assert plan_lot(2, 7).card_count == 6
    assert plan_lot(3, 8).card_count == 6
    assert plan_lot(1501, 1506).card_count == 6

    with pytest.raises(ValueError, match="múltiplo de 6"):
        plan_lot(2, 8)


def test_official_capacity_is_30000() -> None:
    lot = plan_lot(29_995, 30_000)
    assert lot.card_count == 6


def test_generated_lot_can_be_marked_printed_repeatedly(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository)
    lot = service.create_lot(1, 6, CardModel.A, operator="print-test")

    with pytest.raises(ValueError, match="generado"):
        service.mark_printed(lot.lot_id)

    service.generate_lot(lot.lot_id)
    printed = service.mark_printed(lot.lot_id)
    repeated = service.mark_printed(lot.lot_id)

    assert printed.status == "printed"
    assert repeated.status == "printed"
    assert service.get_lot(lot.lot_id).status == "printed"


def test_production_keeps_new_card_layouts_unique_and_non_repetitive(tmp_path) -> None:
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, generator=SeriesGenerator(seed=20260910))
    lot = service.create_lot(1, 600, CardModel.A, operator="uniqueness-test")
    result = service.generate_lot(lot.lot_id)

    assert result.status == "generated"
    cards = repository.get_cards_range(1, 600)
    signatures = {service._layout_signature(card) for card in cards}
    assert len(signatures) == 600

    # La regla de negocio es que cada cartón tenga una distribución distinta.
    # No exigimos una distancia artificialmente alta entre máscaras: con 3x9
    # y 15 números, esa condición puede ser imposible dentro de una serie de 6.
    masks = [service._layout_mask(card) for card in cards]
    for index in range(1, len(masks)):
        previous_window = masks[max(0, index - service.RECENT_LAYOUT_WINDOW):index]
        assert all(
            service._mask_distance(masks[index], previous) >= service.MIN_RECENT_LAYOUT_DISTANCE
            for previous in previous_window
        )
