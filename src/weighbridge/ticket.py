"""Một lượt cân xe: cân lần 1 (xe có hàng) và lần 2 (xe không), trừ tạp chất, ra khối lượng hàng."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class Ticket:
    plate: str                       # biển số xe
    material: str = ""
    gross_kg: int | None = None      # tổng (xe + hàng)
    tare_kg: int | None = None       # bì (xe không)
    impurity_pct: float = 0.0        # trừ tạp chất, đất cát, nước…
    unit_price: int = 0              # đồng/kg
    times: dict[str, str] = field(default_factory=dict)

    def record(self, kg: int, at: datetime | None = None) -> str:
        """Ghi một lần cân. Lần lớn hơn là tổng, nhỏ hơn là bì (xe vào bán hay xe vào mua đều đúng)."""
        at = at or datetime.now()
        if self.gross_kg is None and self.tare_kg is None:
            self.gross_kg = kg
            self.times["lan_1"] = at.isoformat(timespec="seconds")
            return "lan_1"
        first = self.gross_kg if self.gross_kg is not None else self.tare_kg
        assert first is not None
        self.gross_kg, self.tare_kg = max(first, kg), min(first, kg)
        self.times["lan_2"] = at.isoformat(timespec="seconds")
        return "lan_2"

    @property
    def complete(self) -> bool:
        return self.gross_kg is not None and self.tare_kg is not None

    @property
    def net_kg(self) -> int | None:
        if self.gross_kg is None or self.tare_kg is None:
            return None
        return self.gross_kg - self.tare_kg

    @property
    def deduction_kg(self) -> int:
        return 0 if self.net_kg is None else round(self.net_kg * self.impurity_pct / 100)

    @property
    def payable_kg(self) -> int | None:
        return None if self.net_kg is None else self.net_kg - self.deduction_kg

    @property
    def amount(self) -> int | None:
        return None if self.payable_kg is None else self.payable_kg * self.unit_price

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d.update(net_kg=self.net_kg, deduction_kg=self.deduction_kg, payable_kg=self.payable_kg, amount=self.amount)
        return d
