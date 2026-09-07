from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .check import CardCheckService

if TYPE_CHECKING:
    from app.database.series_repository import SQLiteSeriesRepository
    from app.sales.service import SalesService


@dataclass(frozen=True)
class VerificationRecord:
    """Resultado operativo de verificar un cartón por su serial."""

    serial: str
    exists: bool
    series_id: str = ""
    card_index: int = 0
    sold: bool = False
    seller: str = ""
    sale_type: str = ""
    line_rows: tuple[int, ...] = ()
    bingo: bool = False

    @property
    def has_prize(self) -> bool:
        return bool(self.line_rows) or self.bingo


class VerificationService:
    """Une cartón generado, serie, venta y resultado del juego."""

    def __init__(self, repository: SQLiteSeriesRepository, sales: SalesService | None = None) -> None:
        self.repository = repository
        self.sales = sales

    def verify(self, serial: str, called_numbers: set[int] | frozenset[int]) -> VerificationRecord:
        serial = serial.strip()
        if not serial:
            raise ValueError("Debe indicar el número o serial del cartón")

        try:
            card = self.repository.get_card(serial)
            series_id, card_index = self.repository.get_card_position(serial)
        except KeyError as exc:
            raise ValueError(f"El cartón '{serial}' no existe en las series generadas") from exc

        check = CardCheckService.check(card, called_numbers)
        sold = False
        seller = ""
        sale_type = ""
        if self.sales is not None:
            for sale in self.sales.list_sales():
                if sale.sale_type == "carton" and sale.serial == serial:
                    sold, seller, sale_type = True, sale.seller, sale.sale_type
                    break
                if sale.sale_type == "serie" and sale.serial == series_id:
                    sold, seller, sale_type = True, sale.seller, sale.sale_type
                    break

        return VerificationRecord(
            serial=card.serial,
            exists=True,
            series_id=series_id,
            card_index=card_index,
            sold=sold,
            seller=seller,
            sale_type=sale_type,
            line_rows=check.line_rows,
            bingo=check.bingo,
        )
