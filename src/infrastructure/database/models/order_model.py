from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import OrderStatus
from src.infrastructure.database.session import Base


class OrderModel(Base):
    __tablename__ = "orders"

    oid: Mapped[int] = mapped_column(BigInteger, primary_key=True, autoincrement=False)
    owner_address: Mapped[str] = mapped_column(
        String(42), ForeignKey("wallets.address", ondelete="CASCADE"), nullable=False, index=True
    )
    strategy_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("copy_strategies.id", ondelete="SET NULL"), nullable=True, index=True
    )
    asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("assets.asset_id"), nullable=False, index=True
    )
    is_buy: Mapped[bool] = mapped_column(Boolean, nullable=False)
    limit_px: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    sz: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    status: Mapped[OrderStatus] = mapped_column(
        Enum(OrderStatus, name="order_status"), nullable=False, default=OrderStatus.OPEN
    )

    wallet: Mapped["WalletModel"] = relationship(  # noqa: F821
        "WalletModel", foreign_keys=[owner_address], back_populates="orders"
    )
    strategy: Mapped["CopyStrategyModel | None"] = relationship(  # noqa: F821
        "CopyStrategyModel", back_populates="orders"
    )
    asset: Mapped["AssetModel"] = relationship("AssetModel", back_populates="orders")  # noqa: F821
    fills: Mapped[list["FillModel"]] = relationship("FillModel", back_populates="order")  # noqa: F821
