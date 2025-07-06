import json

import requests

GMX_ARBITRUM_TICKERS_URL = "https://arbitrum-api.gmxinfra.io/prices/tickers"

def get_gmx_price_and_funding(token_symbol="BTC"):
    try:
        response = requests.get(GMX_ARBITRUM_TICKERS_URL)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        print(f"Error fetching GMX tickers: {e}")
        return


    print(json.dumps(data, indent=2))

    tickers = data

    for ticker in tickers:
        if ticker.get("tokenSymbol", "").upper() == token_symbol.upper():
            price = ticker.get("minPriceUsd")
            funding_rate = ticker.get("fundingRate")  # Might be None or 0

            print(f"GMX {token_symbol}/USD Spot Info:")
            print(f"  - Min Price (USD): {price}")
            if funding_rate:
                print(f"  - Funding Rate: {funding_rate}%")
            else:
                print("  - Funding Rate not available in REST V2 response.")
            return

    print(f"{token_symbol} not found in GMX tickers.")

if __name__ == "__main__":
    get_gmx_price_and_funding("BTC")
