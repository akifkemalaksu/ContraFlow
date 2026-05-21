import httpx

from src.config import settings


class HyperliquidExchangeAPI:
    """Posts pre-signed actions to Hyperliquid /exchange without holding a private key."""

    async def post_action(self, action: dict, signature: dict, nonce: int) -> dict:
        payload = {
            "action": action,
            "nonce": nonce,
            "signature": signature,
            "vaultAddress": None,
            "expiresAfter": None,
        }
        url = settings.hyperliquid_base_url + "/exchange"
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=payload)
            if response.is_error:
                detail = response.text
                try:
                    detail = str(response.json())
                except Exception:
                    pass
                raise ValueError(
                    f"Hyperliquid rejected the action ({response.status_code}): {detail}"
                )
            return response.json()
