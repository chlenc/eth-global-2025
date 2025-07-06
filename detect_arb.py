import json

from hliq import get_current_funding
from kinch_get_pair import get_pair
from kinch_token_list import fetch_tokens


def quote():
    tks = fetch_tokens()
    rate = get_current_funding()
    #
    RES = {}
    for k, v in tks.items():
        tk_1 = tks[k]
        tk_2 = tks["USDT"]
        # price_usdt = get_pair(tk_1, tk_2)


        token_rate = rate.get(k, None)
        if token_rate is None:
            continue

        result = {}

        result["simbol"] = k
        # result["market_price"] = price_usdt
        result["funding"] = 100*float(token_rate["funding"])
        result["oracle_price"] = token_rate["oraclePx"]
        result["token_rate"] = token_rate

        print(json.dumps(result, indent=4))

        RES[k] = result

    return RES


if __name__ == "__main__":
    qt = quote()

    print(json.dumps(qt, indent=4))
# rate = sort_by_value_desc(rate)
# print(json.dumps(rate, indent=2))
