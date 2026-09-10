from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.cards import CardModel


# Capacidad oficial: 5.000 series × 6 cartones = 30.000 cartones.
DEFAULT_PRODUCTION_CAPACITY = 30_000


@dataclass(frozen=True, slots=True)
class ProductionLot:
    lot_id: int
    start_card: int
    end_card: int
    series_count: int
    model: CardModel
    operator: str = ""
    status: str = "planned"
    created_at: str = ""

    @property
    def card_count(self) -> int:
        return self.end_card - self.start_card + 1


def plan_lot(
    start_card: int,
    end_card: int,
    model: CardModel = CardModel.A,
    lot_id: int = 0,
    operator: str = "",
    max_cards: int = DEFAULT_PRODUCTION_CAPACITY,
) -> ProductionLot:
    if max_cards < 1:
        raise ValueError("La capacidad de producción debe ser positiva")
    if start_card < 1 or end_card < start_card:
        raise ValueError("El rango de cartones no es válido")
    if end_card > max_cards:
        raise ValueError(f"El rango supera la capacidad configurada de {max_cards:,} cartones")
    # The operator can start anywhere: 1, 2, 3, 1501, etc. A print batch
    # remains six cards per logical series/page.
    card_count = end_card - start_card + 1
    if card_count % 6 != 0:
        raise ValueError("La cantidad solicitada debe ser múltiplo de 6 cartones")
    return ProductionLot(
        lot_id=lot_id,
        start_card=start_card,
        end_card=end_card,
        series_count=card_count // 6,
        model=model,
        operator=operator,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
