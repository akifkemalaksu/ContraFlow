# in your main router file or a temp debug file

from fastapi import APIRouter
from eth_account import Account
from eth_account.messages import encode_typed_data
import json

router = APIRouter()

@router.get("/debug/test-agent-recovery")
async def test_agent_recovery():
    r = "dc5dfc6dcc9b174b3aaa8b7978c0db81e872cff9738256ed0c0a7f35f7f5f181"
    s = "30f25cba70f9c5fa746dbb2ae123b8d93524ec3923912b08a0180e699ac5c5b4"
    v = "1b"
    full_sig = "0x" + r + s + v
    expected = "0x21042f560f8a3201de26d4eee180aa1f8df202f0"

    chain_ids   = [
        998,        # HL testnet
        421614,     # Arbitrum Sepolia
        1,          # Ethereum mainnet
        137,        # Polygon
        42161,      # Arbitrum One
        56,         # BSC
        10,         # Optimism
        8453,       # Base
        43114,      # Avalanche
    ]
    agent_names = ["string 3", "string3", "string", ""]
    nonces      = [1779354765281]
    addresses   = [
        "0xd572bde0f7ce45e9880dbccbb92500f591c8f578",
        "0xD572BDE0F7CE45E9880DBCCBB92500F591C8F578",
    ]
    nonce_types = ["uint256", "uint64"]
    hl_chains   = ["Testnet", "testnet"]

    matches = []
    all_results = []

    for chain_id in chain_ids:
        for agent_name in agent_names:
            for nonce in nonces:
                for addr in addresses:
                    for nonce_type in nonce_types:
                        for hl_chain in hl_chains:
                            typed_data = {
                                "domain": {
                                    "name": "HyperliquidSignTransaction",
                                    "version": "1",
                                    "chainId": chain_id,
                                    "verifyingContract": "0x0000000000000000000000000000000000000000"
                                },
                                "types": {
                                    "HyperliquidTransaction:ApproveAgent": [
                                        { "name": "hyperliquidChain", "type": "string"  },
                                        { "name": "agentAddress",     "type": "address" },
                                        { "name": "agentName",        "type": "string"  },
                                        { "name": "nonce",            "type": nonce_type }
                                    ]
                                },
                                "primaryType": "HyperliquidTransaction:ApproveAgent",
                                "message": {
                                    "hyperliquidChain": hl_chain,
                                    "agentAddress": addr,
                                    "agentName": agent_name,
                                    "nonce": nonce
                                }
                            }
                            try:
                                msg = encode_typed_data(full_message=typed_data)
                                recovered = Account.recover_message(msg, signature=full_sig)
                                match = recovered.lower() == expected
                                entry = {
                                    "chainId": chain_id,
                                    "agentName": agent_name,
                                    "address": addr,
                                    "nonce_type": nonce_type,
                                    "hl_chain": hl_chain,
                                    "recovered": recovered,
                                    "match": match
                                }
                                all_results.append(entry)
                                if match:
                                    matches.append(entry)
                            except Exception as e:
                                all_results.append({"error": str(e)})

    return {
        "matches": matches if matches else "NO MATCH FOUND",
        "all_results": all_results,
        "total_combinations_tried": len(all_results)
    }