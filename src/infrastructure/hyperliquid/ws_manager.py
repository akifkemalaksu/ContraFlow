import logging
from collections.abc import Callable
from typing import Any

from src.infrastructure.hyperliquid.client import HyperliquidInfoClient

logger = logging.getLogger(__name__)


class HyperliquidWSManager:
    """Manages WebSocket subscriptions against the Hyperliquid Info WebSocket.

    Subscriptions are identified by the integer ID returned by the SDK.
    Keep an instance alive for the duration of the process.
    """

    def __init__(self, client: HyperliquidInfoClient):
        self._client = client
        self._sub_ids: dict[str, int] = {}

    def subscribe_user_fills(self, address: str, callback: Callable[[Any], None]) -> int:
        key = f"userFills:{address}"
        if key in self._sub_ids:
            return self._sub_ids[key]
        sub_id = self._client.subscribe({"type": "userFills", "user": address}, callback)
        self._sub_ids[key] = sub_id
        logger.info("Subscribed to userFills for %s (id=%d)", address, sub_id)
        return sub_id

    def unsubscribe_user_fills(self, address: str) -> None:
        key = f"userFills:{address}"
        sub_id = self._sub_ids.pop(key, None)
        if sub_id is not None:
            self._client.unsubscribe({"type": "userFills", "user": address}, sub_id)
            logger.info("Unsubscribed from userFills for %s", address)

    def subscribe_all_mids(self, callback: Callable[[Any], None]) -> int:
        key = "allMids"
        if key in self._sub_ids:
            return self._sub_ids[key]
        sub_id = self._client.subscribe({"type": "allMids"}, callback)
        self._sub_ids[key] = sub_id
        logger.info("Subscribed to allMids (id=%d)", sub_id)
        return sub_id

    def unsubscribe_all_mids(self) -> None:
        key = "allMids"
        sub_id = self._sub_ids.pop(key, None)
        if sub_id is not None:
            self._client.unsubscribe({"type": "allMids"}, sub_id)

    def subscribe_order_updates(self, address: str, callback: Callable[[Any], None]) -> int:
        key = f"orderUpdates:{address}"
        if key in self._sub_ids:
            return self._sub_ids[key]
        sub_id = self._client.subscribe({"type": "orderUpdates", "user": address}, callback)
        self._sub_ids[key] = sub_id
        logger.info("Subscribed to orderUpdates for %s (id=%d)", address, sub_id)
        return sub_id

    def unsubscribe_order_updates(self, address: str) -> None:
        key = f"orderUpdates:{address}"
        sub_id = self._sub_ids.pop(key, None)
        if sub_id is not None:
            self._client.unsubscribe({"type": "orderUpdates", "user": address}, sub_id)

    def unsubscribe_all(self) -> None:
        for key in list(self._sub_ids.keys()):
            if key.startswith("userFills:"):
                address = key.removeprefix("userFills:")
                self.unsubscribe_user_fills(address)
            elif key == "allMids":
                self.unsubscribe_all_mids()
            elif key.startswith("orderUpdates:"):
                address = key.removeprefix("orderUpdates:")
                self.unsubscribe_order_updates(address)
        logger.info("All WebSocket subscriptions removed")
