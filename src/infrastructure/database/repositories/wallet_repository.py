from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.wallet import Wallet
from src.domain.repositories.wallet_repository import IWalletRepository
from src.infrastructure.database.models.wallet_model import WalletModel


def _to_domain(model: WalletModel) -> Wallet:
    return Wallet(
        address=model.address,
        user_id=model.user_id,
        name=model.name,
        account_type=model.account_type,
        master_wallet_address=model.master_wallet_address,
        encrypted_agent_private_key=model.encrypted_agent_private_key,
        encryption_iv=model.encryption_iv,
        last_nonce=model.last_nonce,
        is_active=model.is_active,
    )


class WalletRepository(IWalletRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_address(self, address: str) -> Wallet | None:
        result = await self._session.execute(
            select(WalletModel).where(WalletModel.address == address)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_by_user_id(self, user_id: UUID) -> list[Wallet]:
        result = await self._session.execute(
            select(WalletModel).where(WalletModel.user_id == user_id)
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def save(self, wallet: Wallet) -> Wallet:
        model = WalletModel(
            address=wallet.address,
            user_id=wallet.user_id,
            name=wallet.name,
            account_type=wallet.account_type,
            master_wallet_address=wallet.master_wallet_address,
            encrypted_agent_private_key=wallet.encrypted_agent_private_key,
            encryption_iv=wallet.encryption_iv,
            last_nonce=wallet.last_nonce,
            is_active=wallet.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return wallet

    async def update(self, wallet: Wallet) -> Wallet:
        result = await self._session.execute(
            select(WalletModel).where(WalletModel.address == wallet.address)
        )
        model = result.scalar_one()
        model.master_wallet_address = wallet.master_wallet_address
        model.encrypted_agent_private_key = wallet.encrypted_agent_private_key
        model.encryption_iv = wallet.encryption_iv
        model.last_nonce = wallet.last_nonce
        model.is_active = wallet.is_active
        await self._session.flush()
        return wallet

    async def delete(self, address: str) -> None:
        result = await self._session.execute(
            select(WalletModel).where(WalletModel.address == address)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
