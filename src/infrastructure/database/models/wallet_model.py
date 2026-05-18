import uuid

from sqlalchemy import BigInteger, Boolean, Enum, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import AccountType
from src.infrastructure.database.session import Base


class WalletModel(Base):
    __tablename__ = "wallets"

    address: Mapped[str] = mapped_column(String(42), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    master_wallet_address: Mapped[str | None] = mapped_column(
        String(42), ForeignKey("wallets.address", ondelete="SET NULL"), nullable=True
    )
    encrypted_agent_private_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    encryption_iv: Mapped[str | None] = mapped_column(String, nullable=True)
    last_nonce: Mapped[int] = mapped_column(BigInteger, nullable=False, default=0)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="wallets")  # noqa: F821
    master_wallet: Mapped["WalletModel | None"] = relationship(
        "WalletModel", remote_side="WalletModel.address", back_populates="agent_wallets", foreign_keys=[master_wallet_address]
    )
    agent_wallets: Mapped[list["WalletModel"]] = relationship(
        "WalletModel", back_populates="master_wallet", foreign_keys="WalletModel.master_wallet_address"
    )
    strategies: Mapped[list["CopyStrategyModel"]] = relationship(  # noqa: F821
        "CopyStrategyModel", foreign_keys="CopyStrategyModel.user_wallet", back_populates="wallet"
    )
    orders: Mapped[list["OrderModel"]] = relationship(  # noqa: F821
        "OrderModel", foreign_keys="OrderModel.owner_address", back_populates="wallet"
    )
    fills: Mapped[list["FillModel"]] = relationship(  # noqa: F821
        "FillModel", foreign_keys="FillModel.owner_address", back_populates="wallet"
    )
