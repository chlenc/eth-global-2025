import requests

import K1inch
from kinch_token_list import fetch_tokens


def get_pair(TK_1, TK_2):
    url = f"https://api.1inch.dev/price/v1.1/1/{TK_1},{TK_2}"

    headers = {
        "Authorization": f"Bearer {K1inch.API_KEY}"
    }

    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        prices = response.json()
        #print(prices)

        # Convert to lowercase to match JSON keys
        eth_key = TK_1.lower()
        usdt_key = TK_2.lower()

        eth_price_in_usdt = int(prices[eth_key]) / int(prices[usdt_key])
        # print(f"1 ETH ≈ {eth_price_in_usdt:.6f} USDT (Spot Price)")
        return eth_price_in_usdt
    else:
        raise Exception(f"Error {response.status_code}: {response.text}")



# Run it
if __name__ == "__main__":
    tks = fetch_tokens()

    for k in tks:
        tk_1 = tks[k]
        tk_2 = tks["USDT"]
        price = get_pair(tk_1, tk_2)
        print(f"{k}: {price} USDT")
