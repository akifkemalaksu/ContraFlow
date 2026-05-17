from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities.account import Account
from src.domain.repositories.account_repository import IAccountRepository
from src.infrastructure.database.models.account_model import AccountModel


def _to_domain(model: AccountModel) -> Account:
    return Account(
        address=model.address,
        user_id=model.user_id,
        account_type=model.account_type,
        agent_address=model.agent_address,
        encrypted_agent_private_key=model.encrypted_agent_private_key,
        encryption_iv=model.encryption_iv,
        last_nonce=model.last_nonce,
        is_active=model.is_active,
    )


class AccountRepository(IAccountRepository):
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_address(self, address: str) -> Account | None:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.address == address)
        )
        model = result.scalar_one_or_none()
        return _to_domain(model) if model else None

    async def get_by_user_id(self, user_id: UUID) -> list[Account]:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.user_id == user_id)
        )
        return [_to_domain(m) for m in result.scalars().all()]

    async def save(self, account: Account) -> Account:
        model = AccountModel(
            address=account.address,
            user_id=account.user_id,
            account_type=account.account_type,
            agent_address=account.agent_address,
            encrypted_agent_private_key=account.encrypted_agent_private_key,
            encryption_iv=account.encryption_iv,
            last_nonce=account.last_nonce,
            is_active=account.is_active,
        )
        self._session.add(model)
        await self._session.flush()
        return account

    async def update(self, account: Account) -> Account:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.address == account.address)
        )
        model = result.scalar_one()
        model.agent_address = account.agent_address
        model.encrypted_agent_private_key = account.encrypted_agent_private_key
        model.encryption_iv = account.encryption_iv
        model.last_nonce = account.last_nonce
        model.is_active = account.is_active
        await self._session.flush()
        return account

    async def delete(self, address: str) -> None:
        result = await self._session.execute(
            select(AccountModel).where(AccountModel.address == address)
        )
        model = result.scalar_one_or_none()
        if model:
            await self._session.delete(model)
            await self._session.flush()
