from sqlalchemy import BigInteger, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.session import Base


class FillModel(Base):
    __tablename__ = "fills"

    fill_id: Mapped[str] = mapped_column(String(36), primary_key=True)  # UUID stored as string
    oid: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("orders.oid", ondelete="CASCADE"), nullable=False, index=True
    )
    owner_address: Mapped[str] = mapped_column(
        String(42), ForeignKey("wallets.address", ondelete="CASCADE"), nullable=False, index=True
    )
    px: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    sz: Mapped[float] = mapped_column(Numeric(18, 8), nullable=False)
    timestamp: Mapped[int] = mapped_column(BigInteger, nullable=False)

    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="fills")  # noqa: F821
    wallet: Mapped["WalletModel"] = relationship(  # noqa: F821
        "WalletModel", foreign_keys=[owner_address], back_populates="fills"
    )
