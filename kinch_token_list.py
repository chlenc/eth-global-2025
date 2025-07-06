import json

import requests

import K1inch
from CHAIN_ID import ETHERIUM


def get_chain_id():
    import requests

    method = "get"
    apiUrl = "https://api.1inch.dev/token/v1.3/multi-chain/supported-chains"
    headers = {
      "accept": "application/json",
      "Authorization": f"Bearer {K1inch.API_KEY}"
    }

    response = requests.get(apiUrl, headers=headers)


    print(response.json())

def fetch_tokens():
    CHAIN_ID = ETHERIUM  # Ethereum Mainnet
    BASE_URL = f"https://api.1inch.dev/swap/v6.1/{CHAIN_ID}"
    TOKEN_LIST_URL = f"{BASE_URL}/tokens"

    headers = {
      "accept": "application/json",
      "Authorization": f"Bearer {K1inch.API_KEY}"
    }

    response = requests.get(TOKEN_LIST_URL, headers=headers)

    tokens = response.json()["tokens"]

    # print(json.dumps(tokens, indent=2))
    result = {}
    # Lookup address by symbol
    for address, token in tokens.items():
        result[token["symbol"]] = address
    return result
