import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text

from src.main import app
from src.infrastructure.database.session import AsyncSessionFactory


@pytest.fixture(scope="session", autouse=True)
async def clean_db():
    async with AsyncSessionFactory() as session:
        await session.execute(text("TRUNCATE TABLE user_roles, api_keys, users, roles RESTART IDENTITY CASCADE"))
        await session.commit()


@pytest.fixture(scope="session")
async def client(clean_db):
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
