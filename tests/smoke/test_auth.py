import eth_account
import pytest
from eth_account.messages import encode_defunct
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_login_me(client: AsyncClient):
    email = "smoke@example.com"
    password = "SmokeTest123!"

    reg = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert reg.status_code == 201
    assert reg.json()["email"] == email

    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    assert login.status_code == 200
    tokens = login.json()
    assert "access_token" in tokens

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"] == email


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "nonexistent@example.com", "password": "wrong"},
    )
    assert login.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    email = "duplicate@example.com"
    password = "Duplicate123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})

    r = await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    assert r.status_code == 409


@pytest.mark.asyncio
async def test_me_unauthenticated(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_token_refresh(client: AsyncClient):
    email = "refresh@example.com"
    password = "Refresh123!"
    await client.post("/api/v1/auth/register", json={"email": email, "password": password})
    login = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    refresh_token = login.json()["refresh_token"]

    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert r.status_code == 200
    body = r.json()
    assert "access_token" in body
    assert "refresh_token" in body


@pytest.mark.asyncio
async def test_token_refresh_invalid(client: AsyncClient):
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": "not-a-valid-token"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wallet_auth_challenge_verify_me(client: AsyncClient):
    acct = eth_account.Account.create()

    challenge = await client.post(
        "/api/v1/auth/wallet/challenge",
        json={"address": acct.address},
    )
    assert challenge.status_code == 200
    message = challenge.json()["message"]

    signed = acct.sign_message(encode_defunct(text=message))
    signature = signed.signature.hex()
    if not signature.startswith("0x"):
        signature = "0x" + signature

    verify = await client.post(
        "/api/v1/auth/wallet/verify",
        json={"address": acct.address, "message": message, "signature": signature},
    )
    assert verify.status_code == 200
    tokens = verify.json()
    assert "access_token" in tokens

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {tokens['access_token']}"},
    )
    assert me.status_code == 200
    assert me.json()["email"].endswith("@contraflow.invalid")
