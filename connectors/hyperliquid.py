import requests, datetime as dt, pandas as pd
from typing import List, Dict
from eth_account import Account
from hyperliquid.exchange import Exchange
from hyperliquid.utils import constants
from utils.print_funding_rate_table import print_hyperliquid_markets_table

API = "https://api.hyperliquid.xyz/info"

def fetch_hyperliquid_markets() -> List[Dict]:
    """
    Gets data about all perpetual markets on Hyperliquid
    Returns a list of dictionaries with information about each market
    """
    # 1️⃣   All perp markets + price, current funding, 24-hour volume
    meta_ctx = requests.post(API, json={"type": "metaAndAssetCtxs"}).json()
    coins      = meta_ctx[0]["universe"]          # list of dictionaries with {"name": ...}
    asset_ctxs = meta_ctx[1]                      # one-to-one with coins

    # 2️⃣   When funding will update (nextFundingTime)
    pred = requests.post(API, json={"type": "predictedFundings"}).json()
    nft_map = {}
    for coin, venues in pred:                     # [[ "AVAX", [[venue, {...}], ... ]], ...]
        for venue, data in venues:
            if venue == "HlPerp":                 # interested in Hyperliquid itself
                nft_map[coin] = int(data["nextFundingTime"]) // 1000  # ms → sec
                break

    rows = []
    for coin, ctx in zip(coins, asset_ctxs):
        ts = nft_map.get(coin["name"])
        next_funding_time = None
        if ts:
            # Convert UTC timestamp to local time
            utc_time = dt.datetime.utcfromtimestamp(ts)
            # Add offset for Moscow time (UTC+3)
            local_time = utc_time + dt.timedelta(hours=3)
            next_funding_time = local_time
        
        rows.append({
            "coin"          : coin["name"],
            "mark_px"       : float(ctx["markPx"]),      # current price
            "funding_rate"  : float(ctx["funding"]),     # hourly rate (fraction, not %)
            "volume_24h_usd": float(ctx["dayNtlVlm"]),   # volume (USD notional)
            "next_funding_time": next_funding_time
        })
    
    rows.sort(key=lambda x: x['funding_rate'], reverse=True)
    return rows



def open_short(
    secret_key: str,
    coin: str,
    size: float,
    *,
    slippage: float = 0.02,           # 2 % макс. проскальзывания
    testnet: bool = False
) -> dict:

    wallet = Account.from_key(secret_key)

    url = constants.TESTNET_API_URL if testnet else constants.MAINNET_API_URL

    exchange = Exchange(wallet, base_url=url, skip_ws=True)


    order_resp = exchange.market_open(
        name=coin,
        is_buy=False,          # False == sell == SHORT
        sz=size,
        slippage=slippage
    )
    return order_resp

# Для обратной совместимости
if __name__ == "__main__":
    print("🔍 Loading data from Hyperliquid...")
    markets = fetch_hyperliquid_markets()
    print_hyperliquid_markets_table(markets)