from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt

from src.config import settings


class JWTService:
    def create_access_token(self, subject: str, roles: list[str]) -> str:
        expire = datetime.now(UTC) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        return jwt.encode(
            {"sub": subject, "roles": roles, "exp": expire, "type": "access"},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def create_refresh_token(self, subject: str) -> str:
        expire = datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        return jwt.encode(
            {"sub": subject, "exp": expire, "type": "refresh"},
            settings.SECRET_KEY,
            algorithm=settings.ALGORITHM,
        )

    def decode_token(self, token: str) -> dict:
        try:
            return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except JWTError as e:
            raise ValueError(f"Invalid token: {e}") from e
