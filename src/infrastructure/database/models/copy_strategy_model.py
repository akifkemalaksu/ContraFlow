from sqlalchemy import Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import Direction
from src.infrastructure.database.session import Base


class CopyStrategyModel(Base):
    __tablename__ = "copy_strategies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_wallet: Mapped[str] = mapped_column(
        String(42), ForeignKey("accounts.address", ondelete="CASCADE"), nullable=False, index=True
    )
    target_wallet: Mapped[str] = mapped_column(String(42), nullable=False, index=True)
    direction: Mapped[Direction] = mapped_column(
        Enum(Direction, name="direction"), nullable=False
    )
    copy_ratio: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    markup_pct: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False, default=0)
    pnl_control_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    account: Mapped["AccountModel"] = relationship(  # noqa: F821
        "AccountModel", foreign_keys=[user_wallet], back_populates="strategies"
    )
    orders: Mapped[list["OrderModel"]] = relationship("OrderModel", back_populates="strategy")  # noqa: F821
    triggers: Mapped[list["CrossAssetTriggerModel"]] = relationship(  # noqa: F821
        "CrossAssetTriggerModel", back_populates="strategy"
    )
