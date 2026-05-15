from pydantic import BaseModel, EmailStr


class UserCreateDTO(BaseModel):
    email: EmailStr
    password: str


class TokenPairDTO(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class APIKeyCreateDTO(BaseModel):
    scopes: list[str] = []
    expires_in_days: int | None = None
