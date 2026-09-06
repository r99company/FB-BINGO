from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone

from app.cards import CardModel


DEFAULT_PRODUCTION_CAPACITY = 15_000


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
    if (start_card - 1) % 6 != 0 or end_card % 6 != 0:
        raise ValueError("El lote debe comenzar y terminar en límites completos de serie de 6 cartones")
    return ProductionLot(
        lot_id=lot_id,
        start_card=start_card,
        end_card=end_card,
        series_count=(end_card - start_card + 1) // 6,
        model=model,
        operator=operator,
        created_at=datetime.now(timezone.utc).isoformat(),
    )
