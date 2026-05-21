from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.application.use_cases.add_master_wallet import AddMasterWalletUseCase
from src.application.use_cases.complete_agent_wallet import CompleteAgentWalletUseCase
from src.application.use_cases.get_agent_wallets import GetAgentWalletsUseCase
from src.application.use_cases.get_wallet_info import GetWalletInfoUseCase
from src.application.use_cases.initiate_agent_wallet import InitiateAgentWalletUseCase
from src.application.use_cases.login_user import LoginUseCase
from src.application.use_cases.register_user import RegisterUserUseCase
from src.config import settings
from src.infrastructure.database.repositories.wallet_repository import WalletRepository
from src.infrastructure.database.repositories.user_repository import UserRepository
from src.infrastructure.database.session import get_db_session
from src.infrastructure.hyperliquid.client import HyperliquidInfoClient
from src.infrastructure.hyperliquid.exchange_api import HyperliquidExchangeAPI
from src.infrastructure.security.aes_encryptor import AESKeyEncryptor
from src.infrastructure.security.bcrypt_hasher import BcryptPasswordHasher
from src.infrastructure.security.jwt_service import JWTService

_hl_client = HyperliquidInfoClient(skip_ws=True)
_hl_exchange_api = HyperliquidExchangeAPI()
_hasher = BcryptPasswordHasher()
_token_svc = JWTService()
_key_encryptor = AESKeyEncryptor(settings.WALLET_ENCRYPTION_KEY)


def get_token_service() -> JWTService:
    return _token_svc


def get_user_repo(session: AsyncSession = Depends(get_db_session)) -> UserRepository:
    return UserRepository(session)


def get_register_use_case(session: AsyncSession = Depends(get_db_session)) -> RegisterUserUseCase:
    return RegisterUserUseCase(UserRepository(session), _hasher)


def get_login_use_case(session: AsyncSession = Depends(get_db_session)) -> LoginUseCase:
    return LoginUseCase(UserRepository(session), _hasher, _token_svc)


def get_wallet_repo(session: AsyncSession = Depends(get_db_session)) -> WalletRepository:
    return WalletRepository(session)


def get_add_master_wallet_use_case(session: AsyncSession = Depends(get_db_session)) -> AddMasterWalletUseCase:
    return AddMasterWalletUseCase(WalletRepository(session))


def get_wallet_info_use_case(session: AsyncSession = Depends(get_db_session)) -> GetWalletInfoUseCase:
    return GetWalletInfoUseCase(WalletRepository(session), _hl_client)


def get_initiate_agent_wallet_use_case(session: AsyncSession = Depends(get_db_session)) -> InitiateAgentWalletUseCase:
    return InitiateAgentWalletUseCase(WalletRepository(session), _key_encryptor)


def get_complete_agent_wallet_use_case(session: AsyncSession = Depends(get_db_session)) -> CompleteAgentWalletUseCase:
    return CompleteAgentWalletUseCase(WalletRepository(session), _hl_exchange_api)


def get_agent_wallets_use_case(session: AsyncSession = Depends(get_db_session)) -> GetAgentWalletsUseCase:
    return GetAgentWalletsUseCase(WalletRepository(session), _hl_client)
