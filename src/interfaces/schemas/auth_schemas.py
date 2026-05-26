from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, EmailStr

from src.interfaces.schemas.wallet_schemas import ChecksumAddress


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class WalletChallengeRequest(BaseModel):
    address: ChecksumAddress


class WalletChallengeResponse(BaseModel):
    address: str
    message: str


class WalletVerifyRequest(BaseModel):
    address: ChecksumAddress
    message: str
    signature: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    roles: list[str]
    is_active: bool
    created_at: datetime

