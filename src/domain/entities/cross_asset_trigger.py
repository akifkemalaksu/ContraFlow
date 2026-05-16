from dataclasses import dataclass

from decimal import Decimal

from src.domain.enums import Operator


@dataclass
class CrossAssetTrigger:
    strategy_id: int  # FK -> copy_strategies.id
    ref_asset_id: int  # FK -> assets.asset_id (e.g. BTC = 0)
    operator: Operator
    threshold_px: Decimal  # trigger price
    close_pct: Decimal  # percentage of position to close (e.g. 20 = 20%)
    id: int | None = None

    def is_fired(self, current_px: Decimal) -> bool:
        if self.operator == Operator.GT:
            return current_px > self.threshold_px
        return current_px < self.threshold_px
