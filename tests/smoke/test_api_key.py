import pytest
from httpx import AsyncClient


async def _get_token(client: AsyncClient) -> str:
    email = "apikey_smoke@example.com"
    password = "APIKey123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return login.json()["access_token"]


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
    token = await _get_token(client)
    auth_headers = {"Authorization": f"Bearer {token}"}

    created = await client.post("/api/v1/api-keys/", json={}, headers=auth_headers)
    key_id = created.json()["id"]
    raw_key = created.json()["raw_key"]

    revoke = await client.delete(f"/api/v1/api-keys/{key_id}", headers=auth_headers)
    assert revoke.status_code == 204

    me = await client.get("/api/v1/auth/me", headers={"X-API-Key": raw_key})
    assert me.status_code == 401
