#!/usr/bin/env python3


from __future__ import annotations

import argparse
import json
import sys
from typing import Dict, List, Tuple

import requests

API_URL: str = "https://api.hyperliquid.xyz/info"
TIMEOUT: int = 10  # seconds


def _post(payload: Dict) -> dict | list:
    """Helper that POSTs JSON and returns parsed response, raising for HTTP errors."""
    rsp = requests.post(API_URL, json=payload, timeout=TIMEOUT)
    rsp.raise_for_status()
    return rsp.json()


def get_current_funding():
    """Return the *current* 8‑hour funding rate for ``symbol`` (e.g. "ETH")."""
    meta, asset_ctxs = _post({"type": "metaAndAssetCtxs"})
    # print(json.dumps(asset_ctxs, indent=2))
    # print(json.dumps(meta, indent=2))

    result = {}

    # `meta["universe"]` and `asset_ctxs` share the same ordering.
    for idx, ctx in enumerate(asset_ctxs):
        coin = meta["universe"][idx]["name"].upper()
        result[coin] = ctx

    return result

def sort_by_value_desc(d: dict) -> dict:
    # float(ctx["funding"])
    return dict(sorted(d.items(), key=lambda kv: abs(float(kv[1]["funding"])), reverse=True))


def print_funding():
    rate = get_current_funding()
    print(json.dumps(rate, indent=2))
    rate = sort_by_value_desc(rate)
    print(json.dumps(rate, indent=2))


def main() -> None:
        print_funding()



if __name__ == "__main__":
    main()
