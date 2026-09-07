from app.cards import CardModel, SeriesGenerator
from app.database import SQLiteSeriesRepository
from app.printing import A4SvgRenderer, PrintStyle
from app.production import ProductionService


def test_generated_series_survives_database_roundtrip_and_a4_render(tmp_path):
    repository = SQLiteSeriesRepository(tmp_path / "bingo.sqlite3")
    service = ProductionService(repository, max_cards=15_000)
    lot = service.create_lot(1, 6, CardModel.A, operator="test")
    service.generate_lot(lot.lot_id)

    stored = repository.get("0001")
    svg = A4SvgRenderer(style=PrintStyle(show_qr_zone=False)).render(stored.cards)

    assert len(stored.cards) == 6
    assert [card.serial for card in stored.cards] == [f"0001-{i:06d}" for i in range(1, 7)]
    assert sorted(n for card in stored.cards for n in card.numbers) == list(range(1, 91))
    for card in stored.cards:
        assert card.serial in svg
        for number in card.numbers:
            assert f">{number}</text>" in svg


def test_renderer_rejects_a_series_with_missing_card():
    series = SeriesGenerator(seed=20260908).generate("0002", CardModel.A, serial_start=7)
    renderer = A4SvgRenderer()

    try:
        renderer.render(series.cards[:5])
    except ValueError as exc:
        assert "exactly 6" in str(exc)
    else:
        raise AssertionError("A4 renderer accepted an incomplete series")
