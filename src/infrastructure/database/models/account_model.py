import uuid

from sqlalchemy import Boolean, Enum, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.domain.enums import AccountType
from src.infrastructure.database.session import Base


class AccountModel(Base):
    __tablename__ = "accounts"

    address: Mapped[str] = mapped_column(String(42), primary_key=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    agent_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    account_type: Mapped[AccountType] = mapped_column(
        Enum(AccountType, name="account_type"), nullable=False
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    user: Mapped["UserModel"] = relationship("UserModel", back_populates="accounts")  # noqa: F821
    strategies: Mapped[list["CopyStrategyModel"]] = relationship(  # noqa: F821
        "CopyStrategyModel", foreign_keys="CopyStrategyModel.user_wallet", back_populates="account"
    )
    orders: Mapped[list["OrderModel"]] = relationship(  # noqa: F821
        "OrderModel", foreign_keys="OrderModel.owner_address", back_populates="account"
    )
    fills: Mapped[list["FillModel"]] = relationship(  # noqa: F821
        "FillModel", foreign_keys="FillModel.owner_address", back_populates="account"
    )
