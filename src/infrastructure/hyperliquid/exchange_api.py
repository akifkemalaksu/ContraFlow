import asyncio

import httpx

from src.config import settings


class HyperliquidExchangeAPI:
    """Posts pre-signed actions to Hyperliquid /exchange without holding a private key."""

    async def post_action(self, action: dict, signature: dict, nonce: int) -> dict:
        payload = {
            "action": action,
            "nonce": nonce,
            "signature": signature,
        }
        url = settings.hyperliquid_base_url + "/exchange"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            return response.json()
