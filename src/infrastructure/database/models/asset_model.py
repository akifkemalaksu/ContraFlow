from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.infrastructure.database.session import Base


class AssetModel(Base):
    __tablename__ = "assets"

    asset_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=False)
    symbol: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    sz_decimals: Mapped[int] = mapped_column(Integer, nullable=False)
    is_perp: Mapped[bool] = mapped_column(Boolean, nullable=False)

    orders: Mapped[list["OrderModel"]] = relationship("OrderModel", back_populates="asset")  # noqa: F821
    cross_asset_triggers: Mapped[list["CrossAssetTriggerModel"]] = relationship(  # noqa: F821
        "CrossAssetTriggerModel", back_populates="ref_asset"
    )
