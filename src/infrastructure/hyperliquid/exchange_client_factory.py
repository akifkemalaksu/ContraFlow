from src.domain.services.exchange_client import IExchangeClient, IExchangeClientFactory
from src.infrastructure.hyperliquid.exchange_client import HyperliquidExchangeClient


class HyperliquidExchangeClientFactory(IExchangeClientFactory):
    def create(self, private_key: str, account_address: str | None = None) -> IExchangeClient:
        return HyperliquidExchangeClient(private_key, account_address=account_address)
