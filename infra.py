from K1inch import INFRA_PROJECT_ID

NETWORK = "polygon"  # "sepolia"

def eth_infra_rpc(network):
    """
    Returns the correct Infura RPC URL for the given Ethereum network.

    :param network: The Ethereum network name (e.g., "mainnet", "sepolia").
    :return: The Infura RPC URL for the specified network.
    """
    infra = {
        "mainnet": f"https://mainnet.infura.io/v3/{INFRA_PROJECT_ID}",
        "sepolia": f"https://sepolia.infura.io/v3/{INFRA_PROJECT_ID}",
        "goerli": f"https://goerli.infura.io/v3/{INFRA_PROJECT_ID}",
        "rinkeby": f"https://rinkeby.infura.io/v3/{INFRA_PROJECT_ID}",
        "ropsten": f"https://ropsten.infura.io/v3/{INFRA_PROJECT_ID}",
        "polygon": f"https://polygon-mainnet.infura.io/v3/{INFRA_PROJECT_ID}",
        "arbitrum": f"https://arbitrum-mainnet.infura.io/v3/{INFRA_PROJECT_ID}",
        "optimism": f"https://optimism-mainnet.infura.io/v3/{INFRA_PROJECT_ID}"
    }

    if network in infra:
        return infra[network]
    else:
        raise ValueError(f"Unsupported network: {network}. Available networks: {list(infra.keys())}")

