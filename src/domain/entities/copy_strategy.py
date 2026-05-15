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
