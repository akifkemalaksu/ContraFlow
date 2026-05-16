from datetime import datetime, timedelta, timezone

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from src.domain.entities.user import User
from src.infrastructure.database.session import AsyncSessionFactory
from src.interfaces.api.v1.dependencies.auth import require_api_key_scopes


async def _get_token(client: AsyncClient, suffix: str = "") -> str:
    email = f"apikey_smoke{suffix}@example.com"
    password = "APIKey123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]


@pytest.fixture(scope="session")
async def scope_client():
    mini = FastAPI()

    @mini.get("/write-only")
    async def _endpoint(user: User = require_api_key_scopes(["write"])):
        return {"ok": True}

    async with AsyncClient(transport=ASGITransport(app=mini), base_url="http://test") as c:
        yield c


@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient):
    token = await _get_token(client, "_list")
    auth_headers = {"Authorization": f"Bearer {token}"}

    await client.post("/api/v1/api-keys/", json={"scopes": ["read"]}, headers=auth_headers)
    await client.post("/api/v1/api-keys/", json={"scopes": ["write"]}, headers=auth_headers)

    r = await client.get("/api/v1/api-keys/", headers=auth_headers)
    assert r.status_code == 200
    assert len(r.json()) >= 2


@pytest.mark.asyncio
async def test_create_and_use_api_key(client: AsyncClient):
    token = await _get_token(client)
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/api-keys/", json={"scopes": ["read"]}, headers=auth_headers)
    assert created.status_code == 201
    raw_key = created.json()["raw_key"]
    assert raw_key

    me = await client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
    assert me.status_code == 200


@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient):
    token = await _get_token(client, "_revoke")
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/api-keys/", json={}, headers=auth_headers)
    key_id = created.json()["id"]
    raw_key = created.json()["raw_key"]

    revoke = await client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
    assert revoke.status_code == 204

    me = await client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_jwt_only_endpoint_rejects_api_key(client: AsyncClient):
    token = await _get_token(client, "_jwt_only")
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/api-keys/", json={"scopes": ["read"]}, headers=auth_headers)
    raw_key = created.json()["raw_key"]

    # POST /api-keys/ requires JWT — an API key alone must be rejected
    r = await client.post(
        "/api/v1/api-keys/",
        json={"scopes": ["read"]},
        headers={"X-API-Key": raw_key},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_expired_api_key_rejected(client: AsyncClient):
    token = await _get_token(client, "_expired")
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/api-keys/", json={"scopes": ["read"]}, headers=auth_headers)
    key_id = created.json()["id"]
    raw_key = created.json()["raw_key"]

    async with AsyncSessionFactory() as session:
        await session.execute(
            text("UPDATE api_keys SET expires_at = :exp WHERE id = :id"),
            {"exp": datetime.now(timezone.utc) - timedelta(hours=1), "id": key_id},
        )
        await session.commit()

    me = await client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
    assert me.status_code == 401


@pytest.mark.asyncio
async def test_api_key_wrong_scope_rejected(client: AsyncClient, scope_client: AsyncClient):
    token = await _get_token(client, "_scope_wrong")
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/api-keys/", json={"scopes": ["read"]}, headers=auth_headers
    )
    raw_key = created.json()["raw_key"]

    r = await scope_client.get("/write-only", headers={"X-API-Key": raw_key})
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_api_key_correct_scope_accepted(client: AsyncClient, scope_client: AsyncClient):
    token = await _get_token(client, "_scope_right")
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/api-keys/", json={"scopes": ["write"]}, headers=auth_headers
    )
    raw_key = created.json()["raw_key"]

    r = await scope_client.get("/write-only", headers={"X-API-Key": raw_key})
    assert r.status_code == 200
