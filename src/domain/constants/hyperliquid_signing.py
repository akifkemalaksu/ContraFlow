"""Hyperliquid user-signed action params — matches hyperliquid-python-sdk sign_user_signed_action."""

# SDK sets signatureChainId to 0x66eee (Arbitrum Sepolia) for ApproveAgent on both mainnet and testnet.
HL_SIGNATURE_CHAIN_ID_HEX = "0x66eee"

APPROVE_AGENT_PAYLOAD_TYPES = [
    {"name": "hyperliquidChain", "type": "string"},
    {"name": "agentAddress", "type": "address"},
    {"name": "agentName", "type": "string"},
    {"name": "nonce", "type": "uint64"},
]
