import datetime as dt
import hashlib
import json
from typing import List, Dict

import K1inch

API = "https://api.hyperliquid.xyz/info"


def fetch_hyperliquid_markets() -> List[Dict]:
    """
    Gets data about all perpetual markets on Hyperliquid
    Returns a list of dictionaries with information about each market
    """
    # 1️⃣   All perp markets + price, current funding, 24-hour volume
    meta_ctx = requests.post(API, json={"type": "metaAndAssetCtxs"}).json()
    coins = meta_ctx[0]["universe"]  # list of dictionaries with {"name": ...}
    asset_ctxs = meta_ctx[1]  # one-to-one with coins

    # 2️⃣   When funding will update (nextFundingTime)
    pred = requests.post(API, json={"type": "predictedFundings"}).json()
    nft_map = {}
    for coin, venues in pred:  # [[ "AVAX", [[venue, {...}], ... ]], ...]
        for venue, data in venues:
            if venue == "HlPerp":  # interested in Hyperliquid itself
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
            "coin": coin["name"],
            "mark_px": float(ctx["markPx"]),  # current price
            "funding_rate": float(ctx["funding"]),  # hourly rate (fraction, not %)
            "volume_24h_usd": float(ctx["dayNtlVlm"]),  # volume (USD notional)
            "next_funding_time": next_funding_time
        })

    rows.sort(key=lambda x: x['funding_rate'], reverse=True)
    return rows


def post(params, coin):
    return {
        "status": "ok",
        "data": {
            "order": {
                "coin": coin,
                "isBuy": False,
                "sz": "0.0335",
                "limitPx": "",
                "orderType": "limit",
                "reduceOnly": False,
                "timestamp": 1720000000000,
                "oid": "abc123xyz789",
                "status": "submitted"
            }
        }
    }


def format_time_until_funding(next_funding_time: dt.datetime) -> str:
    """Formats time until next funding in human-readable format"""
    if not next_funding_time:
        return "N/A"

    now = dt.datetime.now()  # Use local time instead of UTC
    time_diff = next_funding_time - now

    if time_diff.total_seconds() < 0:
        # If time has already passed, show how many minutes ago
        abs_diff = abs(time_diff.total_seconds())
        minutes_ago = int(abs_diff // 60)
        if minutes_ago < 60:
            return f"in {minutes_ago}m"
        else:
            hours_ago = int(minutes_ago // 60)
            minutes_ago = minutes_ago % 60
            return f"in {hours_ago}h {minutes_ago}m"

    hours = int(time_diff.total_seconds() // 3600)
    minutes = int((time_diff.total_seconds() % 3600) // 60)

    if hours > 0:
        return f"in {hours}h {minutes}m"
    else:
        return f"in {minutes}m"


def format_volume(volume_usd: float) -> str:
    """Форматирует объем в человекочитаемом виде"""
    if volume_usd >= 1_000_000_000:  # >= 1B
        return f"${volume_usd / 1_000_000_000:.1f}B"
    elif volume_usd >= 1_000_000:  # >= 1M
        return f"${volume_usd / 1_000_000:.1f}M"
    elif volume_usd >= 1_000:  # >= 1K
        return f"${volume_usd / 1_000:.1f}K"
    else:
        return f"${volume_usd:.0f}"


def format_price(price: float) -> str:
    """Форматирует цену в человекочитаемом виде"""
    if price >= 1000:
        return f"${price:,.0f}"
    elif price >= 1:
        return f"${price:.2f}"
    else:
        return f"${price:.4f}"

def signature(message):
    return hashlib.sha256(message)

def print_hyperliquid_markets_table(markets):
    """Creates and displays a beautiful table with Hyperliquid data"""

    # Take top 10
    top_markets = markets[:10]

    print(f"\n📊 TOP-10 HYPERLIQUID MARKETS BY FUNDING RATE")
    # Statistics
    total_volume = sum(m['volume_24h_usd'] for m in top_markets)
    avg_funding = sum(m['funding_rate'] for m in top_markets) / len(top_markets) * 100

    print(f"   Total 24h Volume: {format_volume(total_volume)}")
    print(f"   Average Funding Rate: {avg_funding:.4f}%")
    print(f"   Highest Funding Rate: {top_markets[0]['funding_rate'] * 100:.4f}% ({top_markets[0]['coin']})")
    print("=" * 110)
    print(f"{'Market':<12} {'Price':<12} {'Funding/hr':<12} {'24h Volume':<12} {'Next Funding':<25}")
    print("-" * 110)

    for market in top_markets:
        coin = market['coin']
        price = format_price(market['mark_px'])
        funding_rate = market['funding_rate'] * 100  # convert to percentage
        volume = format_volume(market['volume_24h_usd'])

        # Format next funding time
        if market['next_funding_time']:
            funding_time_str = market['next_funding_time'].strftime("%H:%M %d.%m")
            time_until = format_time_until_funding(market['next_funding_time'])
            next_funding_display = f"{funding_time_str} ({time_until})"
        else:
            next_funding_display = "N/A"

        # Color indicator for funding rate and coin name
        if funding_rate > 0.01:  # > 1%
            coin_display = f"🟢 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        elif funding_rate > 0.001:  # > 0.1%
            coin_display = f"🟡 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        elif funding_rate < -0.01:  # < -1%
            coin_display = f"🔴 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        elif funding_rate < -0.001:  # < -0.1%
            coin_display = f"🟠 {coin}"
            funding_display = f"{funding_rate:>8.4f}%"
        else:
            coin_display = f"⚪ {coin}"
            funding_display = f"{funding_rate:>8.4f}%"

        print(f"{coin_display:<12} {price:<12} {funding_display:<12} {volume:<12} {next_funding_display:<25}")

    print("-" * 110)

    print()


# Для обратной совместимости
if __name__ == "__main__":
    print("🔍 Loading data from Hyperliquid...")
    markets = fetch_hyperliquid_markets()
    print_hyperliquid_markets_table(markets)

import time
import requests
from web3 import Web3
from eth_account import Account


# Your private key and address


def open_short_position(trade_amount_usdc, coin, current_price):
    # Calculate quantity based on price
    size = round(trade_amount_usdc / current_price, 5)  # truncate for simplicity
    PRIVATE_KEY = K1inch.PRIVATE_KEY
    ADDRESS = Account.from_key(PRIVATE_KEY).address
    # Prepare the order data
    order = {
        "type": "order",
        "order": {
            "coin": coin,
            "isBuy": False,  # False = Short
            "sz": str(size),
            "limitPx": str(current_price * 1.001),  # slight slippage
            "orderType": "limit",
            "reduceOnly": False
        },
        "timestamp": int(time.time() * 1000),
        "sender": ADDRESS
    }

    # Sign the order using web3 (EIP-191 or similar)
    message = Web3.solidity_keccak(
        ['string'], [str(order)]
    )
    # signed_message = Account.sign_message(Web3.to_bytes(message), private_key=PRIVATE_KEY)
    # signature = signed_message.signature.hex()

    # Send the order
    payload = {
        "type": "order",
        "order": order["order"],
        "sender": ADDRESS,
        "signature": signature(message)
    }
    API_URL = "https://api.hyperliquid.xyz/exchange"
    response = post({"url": API_URL, "payload": payload}, coin)
    if response is not None:
        print("Short position submitted:", response)
        return response
    else:
        print("Error:", "")
        return None
