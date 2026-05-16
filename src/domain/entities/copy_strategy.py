from dataclasses import dataclass, field
from decimal import Decimal

from src.domain.enums import Direction


@dataclass
class CopyStrategy:
    user_wallet: str  # FK -> accounts.address
    target_wallet: str
    direction: Direction
    copy_ratio: Decimal
    id: int | None = None
    markup_pct: Decimal = field(default_factory=lambda: Decimal("0"))
    pnl_control_enabled: bool = False

    def compute_order(
        self,
        target_is_buy: bool,
        target_sz: Decimal,
        target_px: Decimal,
    ) -> tuple[bool, Decimal, Decimal]:
        """Returns (is_buy, sz, limit_px) applying direction, ratio, and markup rules."""
        is_buy = target_is_buy if self.direction == Direction.FORWARD else not target_is_buy
        sz = (target_sz * self.copy_ratio).quantize(Decimal("0.0001"))
        if self.markup_pct != 0:
            factor = 1 + self.markup_pct / 100 if is_buy else 1 - self.markup_pct / 100
            limit_px = (target_px * Decimal(str(factor))).quantize(Decimal("0.00001"))
        else:
            limit_px = target_px
        return is_buy, sz, limit_px
