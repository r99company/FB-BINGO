from pathlib import Path

import pytest

from app.sales import SalesService


def test_sales_service_registers_sale_and_blocks_duplicate(tmp_path: Path):
    service = SalesService(tmp_path / "fb-bingo.db")

    sale = service.sell("C-00047", sale_type="carton", seller="Vendedor 1")

    assert sale.serial == "C-00047"
    assert service.is_sold("C-00047")
    with pytest.raises(ValueError, match="ya fue vendido"):
        service.sell("C-00047", sale_type="carton")


def test_sales_service_lists_series_and_cartons(tmp_path: Path):
    service = SalesService(tmp_path / "fb-bingo.db")
    service.sell("S-001", sale_type="serie")
    service.sell("C-00001", sale_type="carton")

    assert {sale.serial for sale in service.list_sales()} == {"S-001", "C-00001"}
