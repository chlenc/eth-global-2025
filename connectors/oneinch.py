from __future__ import annotations

import math
import os
import time
from typing import Any, Dict, List, Optional

# Apply patch for eth_account.messages before importing limit_order_sdk
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from utils.eth_account_patch import *

import requests
from eth_account import Account
from web3 import Web3
from limit_order_sdk import (
    Address,
    Api,
    ApiConfig,
    FetchProviderConnector,
    LimitOrder,
    MakerTraits,
    OrderInfoData,
)

# -----------------------------------------------------------------------------
BASE_URL_TEMPLATE = "https://api.1inch.dev/orderbook/v4.0/{chain_id}"


def get_markets(
    chain_id: int,
    *,
    limit: int = 250,
    api_key: str | None = None,
) -> List[Dict[str, Any]]:
    """Return markets (pairs) that currently have at least one active order."""
    api_key = api_key or os.getenv("ONEINCH_API_KEY")
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    url = f"{BASE_URL_TEMPLATE.format(chain_id=chain_id)}/markets"
    res = requests.get(url, params={"limit": limit}, headers=headers, timeout=10)
    res.raise_for_status()
    return res.json().get("items", [])


def place_limit_order(
    *,
    chain_id: int,
    private_key: str,
    maker_token: str,
    taker_token: str,
    maker_amount: int,
    taker_amount: int,
    api_key: str | None = None,
    ttl_seconds: int = 3600,
) -> str:
    """Sign and broadcast a limit order. Returns its hash."""
    api_key = api_key or os.getenv("ONEINCH_API_KEY")
    wallet = Account.from_key(private_key)

    expiration = math.floor(time.time()) + ttl_seconds
    traits = MakerTraits.default().with_expiration(expiration)

    order_data = OrderInfoData(
        maker_asset=Address(maker_token),
        taker_asset=Address(taker_token),
        making_amount=maker_amount,
        taking_amount=taker_amount,
        maker=Address(wallet.address),
    )
    order = LimitOrder(order_data, traits)
    typed = order.get_typed_data(chain_id)
    signed = Account.sign_typed_data(
        private_key,
        typed.domain,
        {"Order": typed.types["Order"]},
        typed.message,
    )

    api_cfg = ApiConfig(
        chain_id=chain_id,
        auth_key=api_key,
        http_connector=FetchProviderConnector(),
    )
    Api(api_cfg).submit_order(order, signed.signature.hex())

    return order.get_order_hash(chain_id)


class OneInchSwapConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.1inch.dev"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
    
    def get_supported_tokens(self, chain_id: int = 42161) -> Dict[str, str]:
        """
        Get list of supported tokens on Arbitrum (chain_id=42161)
        
        Args:
            chain_id: Chain ID (42161 for Arbitrum)
            
        Returns:
            Dictionary with symbol as key and address as value
        """
        try:
            url = f"{self.base_url}/swap/v5.2/{chain_id}/tokens"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            tokens = data.get("tokens", {})
            
            # Convert to format: symbol -> address
            result = {}
            for token_address, token_info in tokens.items():
                symbol = token_info.get("symbol", "")
                if symbol:
                    result[symbol] = token_address
            
            return result
            
        except Exception as e:
            print(f"❌ Error getting supported tokens: {e}")
            return {}

