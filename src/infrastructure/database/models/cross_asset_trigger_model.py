from sqlalchemy import Enum, ForeignKey, Integer, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import Operator
from src.infrastructure.database.session import Base


class CrossAssetTriggerModel(Base):
    __tablename__ = "cross_asset_triggers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    strategy_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("copy_strategies.id", ondelete="CASCADE"), nullable=False, index=True
    )
    ref_asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assets.asset_id"), nullable=False
    )
    operator: Mapped[Operator] = mapped_column(
        Enum(Operator, name="operator"), nullable=False
    )
    threshold_px: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    close_pct: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)

    strategy: Mapped["CopyStrategyModel"] = relationship(  # noqa: F821
        "CopyStrategyModel", back_populates="triggers"
    )
    ref_asset: Mapped["AssetModel"] = relationship(  # noqa: F821
        "AssetModel", back_populates="cross_asset_triggers"
    )
