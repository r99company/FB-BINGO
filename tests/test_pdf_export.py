from app.cards import CardModel, SeriesGenerator
from app.printing import A4PdfRenderer, BulkA4PdfExporter


class MemoryRepository:
    def __init__(self, series):
        self._series = {item.series_id: item for item in series}

    def get(self, series_id):
        return self._series[str(series_id)]


def test_a4_pdf_renderer_creates_pdf(tmp_path):
    series = SeriesGenerator(seed=31).generate("1", CardModel.A, serial_start=1)
    target = tmp_path / "serie_0001.pdf"

    A4PdfRenderer().save(series.cards, target)

    data = target.read_bytes()
    assert data.startswith(b"%PDF-")
    assert data.count(b"/Type /Page") == 1


def test_bulk_a4_pdf_export_creates_one_page_per_series(tmp_path):
    generator = SeriesGenerator(seed=32)
    series = tuple(
        generator.generate(str(number), CardModel.B, serial_start=(number - 1) * 6 + 1)
        for number in range(1, 4)
    )
    result = BulkA4PdfExporter(MemoryRepository(series)).export(
        start_series=1,
        quantity=3,
        destination=tmp_path / "fb_bingo_3_series.pdf",
        model=CardModel.B,
    )

    data = result.destination.read_bytes()
    assert result.pages_exported == 3
    assert result.cards_exported == 18
    assert data.startswith(b"%PDF-")
    assert data.count(b"/Type /Page") == 3
