import requests
import json
from typing import Dict, Optional
from web3 import Web3
import os

import K1inch
from CHAIN_ID import ARBITRUM
from oneInch_swap import OneInchClient

# Arbitrum RPC endpoints
ARBITRUM_RPC = "https://arb1.arbitrum.io/rpc"

# Token contract addresses on Arbitrum
USDC_CONTRACT_ADDRESS = "0xaf88d065e77c8cC2239327C5EDb3A432268e5831"
USDT_CONTRACT_ADDRESS = "0xFd086bC7CD5C481DCC9C85ebE478A1C0b69FCbb9"


# Token ABI (minimal for balance checking)
TOKEN_ABI = [
    {
        "constant": True,
        "inputs": [{"name": "_owner", "type": "address"}],
        "name": "balanceOf",
        "outputs": [{"name": "balance", "type": "uint256"}],
        "type": "function"
    },
    {
        "constant": True,
        "inputs": [],
        "name": "decimals",
        "outputs": [{"name": "", "type": "uint8"}],
        "type": "function"
    }
]

class ArbitrumConnector:
    def __init__(self, rpc_url: str = ARBITRUM_RPC):
        """
        Initialize Arbitrum connector
        
        Args:
            rpc_url: Arbitrum RPC endpoint
        """
        self.rpc_url = rpc_url
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        
        # Check connection
        if not self.w3.is_connected():
            raise Exception(f"Failed to connect to Arbitrum RPC: {rpc_url}")
        
    
    def get_token_balance(self, wallet_address: str, token_address: str) -> Optional[float]:
        """
        Get token balance for a wallet address
        
        Args:
            wallet_address: Wallet address to check
            token_address: Token contract address
            
        Returns:
            Token balance as float, or None if error
        """
        try:
            # Normalize addresses (remove checksum validation)
            normalized_wallet = self.w3.to_checksum_address(wallet_address.lower())
            normalized_token = self.w3.to_checksum_address(token_address.lower())
            
            # Create contract instance
            token_contract = self.w3.eth.contract(
                address=normalized_token,
                abi=TOKEN_ABI
            )
            
            # Get balance
            balance_raw = token_contract.functions.balanceOf(normalized_wallet).call()
            
            # Get decimals
            decimals = token_contract.functions.decimals().call()
            
            # Convert to human readable format
            balance = balance_raw / (10 ** decimals)
            
            return balance
            
        except Exception as e:
            print(f"Error getting token balance: {e}")
            return 0
    
    def get_eth_balance(self, wallet_address: str) -> Optional[float]:
        client = OneInchClient(chain_id=ARBITRUM, private_key=K1inch.PRIVATE_KEY, api_key=K1inch.API_KEY)
        balance = client.web3.eth.get_balance(client.account.address)
        balance_eth = client.web3.from_wei(balance, "ether")
        print(f"Balance: {balance_eth} tokens")
        return balance_eth

    def get_wallet_balances(self, wallet_address: str) -> Dict[str, float]:
        """
        Get ETH, USDC and USDT balances for a wallet
        
        Args:
            wallet_address: Wallet address to check
            
        Returns:
            Dictionary with 'eth', 'usdc' and 'usdt' balances
        """
        balances = {
            'eth': 0.0,
            'usdc': 0.0,
            'usdt': 0.0
        }
        
        # Get ETH balance
        eth_balance = self.get_eth_balance(wallet_address)
        if eth_balance is not None:
            balances['eth'] = eth_balance
        
        # Get USDC balance
        usdc_balance = self.get_token_balance(wallet_address, USDC_CONTRACT_ADDRESS)
        if usdc_balance is not None:
            balances['usdc'] = usdc_balance
        
        # Get USDT balance
        usdt_balance = self.get_token_balance(wallet_address, USDT_CONTRACT_ADDRESS)
        if usdt_balance is not None:
            balances['usdt'] = usdt_balance
        
        return balances
    
    def print_wallet_balances(self, wallet_address: str, wallet_name: str, balances):
        """
        Print wallet balances in a nice format
        
        Args:
            wallet_address: Wallet address to display
        """
        print(f"\n💰 {wallet_name} WALLET BALANCES (Arbitrum)")
        print(f"   Address: {wallet_address}")
        print("-" * 50)
        
        
        print(f"   ETH:  {balances['eth']:.6f}")
        print(f"   USDC: ${balances['usdc']:,.2f}")
        print(f"   USDT: ${balances['usdt']:,.2f}")
        print()


# For testing
if __name__ == "__main__":
    # Example usage
    hyperliquid_wallet_address = os.environ.get("HYPERLIQUID_ADDRESS")
    arbitrum_wallet_address = os.environ.get("ARBITRUM_ADDRESS")
    print("🔍 Testing Arbitrum connector...")
    
    # Test function that prints balances
    connector = ArbitrumConnector(ARBITRUM_RPC)

    balances = connector.get_wallet_balances(hyperliquid_wallet_address)
    connector.print_wallet_balances(hyperliquid_wallet_address, "HYPERLIQUID", balances)

    balances = connector.get_wallet_balances(arbitrum_wallet_address)
    connector.print_wallet_balances(arbitrum_wallet_address, "ARBITRUM", balances)