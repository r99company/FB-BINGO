from app.cards import CardModel, SeriesGenerator
from app.printing import BulkA4SvgExporter


class MemoryRepository:
    def __init__(self, series):
        self._series = {item.series_id: item for item in series}

    def get(self, series_id):
        return self._series[str(series_id)]


def test_bulk_a4_export_creates_one_a4_svg_per_series(tmp_path):
    generator = SeriesGenerator(seed=22)
    series = tuple(generator.generate(str(number), CardModel.A, serial_start=(number - 1) * 6 + 1)
                   for number in range(1, 4))
    repo = MemoryRepository(series)

    progress = []
    result = BulkA4SvgExporter(repo).export(
        start_series=1,
        quantity=3,
        destination=tmp_path,
        model=CardModel.A,
        progress=lambda current, total: progress.append((current, total)),
    )

    assert result.pages_exported == 3
    assert result.first_series == 1
    assert result.last_series == 3
    assert result.cards_exported == 18
    assert progress == [(1, 3), (2, 3), (3, 3)]

    files = sorted(tmp_path.glob("serie_*.svg"))
    assert [path.name for path in files] == ["serie_0001.svg", "serie_0002.svg", "serie_0003.svg"]
    content = files[0].read_text(encoding="utf-8")
    assert '<svg' in content
    assert 'data-serial="1-000001"' in content


def test_bulk_a4_export_rejects_non_positive_quantity(tmp_path):
    generator = SeriesGenerator(seed=1)
    repo = MemoryRepository([generator.generate("1", CardModel.B, serial_start=1)])

    try:
        BulkA4SvgExporter(repo).export(start_series=1, quantity=0, destination=tmp_path)
    except ValueError as exc:
        assert "positivos" in str(exc)
    else:
        raise AssertionError("Se esperaba ValueError")
