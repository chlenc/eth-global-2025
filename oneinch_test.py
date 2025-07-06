"""
One-inch Limit Order Test
=========================
Тестовый файл для демонстрации работы с 1inch API на Arbitrum One.
"""

import os
from web3 import Web3
from eth_account import Account
from connectors.oneinch import get_markets, place_limit_order

# Helpers ---------------------------------------------------------------------
ERC20_BALANCE_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "", "type": "uint256"}],
        "type": "function",
    }
]


def erc20_balance(w3: Web3, token: str, wallet: str) -> int:
    """Return raw token balance."""
    contract = w3.eth.contract(address=Web3.to_checksum_address(token), abi=ERC20_BALANCE_ABI)
    return contract.functions.balanceOf(wallet).call()



def main():
    """Основная функция для тестирования 1inch API."""
    
    # Quick demo on **Arbitrum One**
    CHAIN_ID = 42_161
    RPC_URL = os.getenv("RPC_URL", "https://arb1.arbitrum.io/rpc")
    # USDC native & USDT bridged on Arbitrum
    USDC_ADDRESS = "0xAf88d065e77c8cC2239327C5EDb3A432268e5831"  # 6 decimals
    USDT_ADDRESS = "0xfd086bc7cd5c481dcc9c85ebe478a1c0b69fcbb9"  # 6 decimals

    API_KEY = os.getenv("ONEINCH_API_KEY")
    
    key = os.getenv("ARBITRUM_PRIVATE_KEY")
    if not key:
        raise SystemExit("Set ARBITRUM_PRIVATE_KEY env var first!")

    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    maker = Account.from_key(key)

    print("\n== Balances ==")
    eth_balance = w3.eth.get_balance(maker.address)
    print("ETH:", w3.from_wei(eth_balance, "ether"))
    print("USDC:", erc20_balance(w3, USDC_ADDRESS, maker.address) / 10 ** 6)
    print("USDT:", erc20_balance(w3, USDT_ADDRESS, maker.address) / 10 ** 6)

    print("\n== Active markets ==")
    print(API_KEY)
    markets = get_markets(CHAIN_ID, api_key=API_KEY)
    print(f"{len(markets)} pairs with live orders. Example: {markets[0] if markets else '—'}")

    print("\n== Posting limit order ==")
    MAKER_AMOUNT = 10 * 10 ** 6  # 10 USDC
    TAKER_AMOUNT = 10 * 10 ** 6  # 10 USDT

    order_hash = place_limit_order(
        chain_id=CHAIN_ID,
        private_key=key,
        maker_token=USDC_ADDRESS,
        taker_token=USDT_ADDRESS,
        maker_amount=MAKER_AMOUNT,
        taker_amount=TAKER_AMOUNT,
        api_key=API_KEY,
    )

    print("Order submitted 🎉  Hash:", order_hash)


if __name__ == "__main__":
    main()
