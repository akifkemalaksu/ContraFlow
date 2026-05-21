"""Hyperliquid user-signed ApproveAgent helpers — mirrors hyperliquid-python-sdk."""

from eth_utils import to_checksum_address

from hyperliquid.utils.signing import user_signed_payload

from src.domain.constants.hyperliquid_signing import (
    APPROVE_AGENT_PAYLOAD_TYPES,
    HL_SIGNATURE_CHAIN_ID_HEX,
)

APPROVE_AGENT_PRIMARY_TYPE = "HyperliquidTransaction:ApproveAgent"


def _lower_address(address: str) -> str:
    return to_checksum_address(address).lower()


def _build_approve_agent_action(
    agent_address: str,
    agent_name: str,
    nonce: int,
    *,
    is_mainnet: bool,
) -> dict:
    return {
        "type": "approveAgent",
        "agentAddress": _lower_address(agent_address),
        "agentName": agent_name,
        "nonce": nonce,
        "signatureChainId": HL_SIGNATURE_CHAIN_ID_HEX,
        "hyperliquidChain": "Mainnet" if is_mainnet else "Testnet",
    }


def build_approve_agent_eip712(
    agent_address: str,
    agent_name: str,
    nonce: int,
    *,
    is_mainnet: bool,
) -> dict:
    """Build the EIP-712 typed data payload for MetaMask (primaryType camelCase)."""
    action = _build_approve_agent_action(
        agent_address, agent_name, nonce, is_mainnet=is_mainnet
    )
    data = user_signed_payload(
        APPROVE_AGENT_PRIMARY_TYPE,
        APPROVE_AGENT_PAYLOAD_TYPES,
        action,
    )
    # Only struct fields in message — matches what MetaMask hashes for ApproveAgent.
    message = {
        "hyperliquidChain": action["hyperliquidChain"],
        "agentAddress": action["agentAddress"],
        "agentName": action["agentName"],
        "nonce": action["nonce"],
    }
    return {
        "domain": data["domain"],
        # Omit EIP712Domain — MetaMask eth_signTypedData_v4 expects only struct types.
        "types": {k: v for k, v in data["types"].items() if k != "EIP712Domain"},
        "primaryType": data["primaryType"],
        "message": message,
    }


def build_approve_agent_post_action(
    agent_address: str,
    agent_name: str,
    nonce: int,
    *,
    is_mainnet: bool,
) -> dict:
    """Action object for POST /exchange — same shape as SDK after sign_agent."""
    return _build_approve_agent_action(
        agent_address, agent_name, nonce, is_mainnet=is_mainnet
    )


def split_eip712_signature(sig_hex: str) -> dict:
    """Split a 65-byte EIP-712 hex signature into {r, s, v} for Hyperliquid /exchange."""
    raw = sig_hex.removeprefix("0x")
    if len(raw) != 130:
        raise ValueError("Signature must be 65 bytes (130 hex chars)")
    v = int(raw[128:130], 16)
    if v < 27:
        v += 27
    return {
        "r": "0x" + raw[:64],
        "s": "0x" + raw[64:128],
        "v": v,
    }
