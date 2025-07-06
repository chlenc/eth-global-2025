import requests
import json
from typing import Dict, List, Optional
import os

class OneInchConnector:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.1inch.dev"
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json"
        }
    
    def get_supported_tokens(self, chain_id: int = 42161) -> Dict[str, Dict]:
        """
        Get list of supported tokens on Arbitrum (chain_id=42161)
        
        Args:
            chain_id: Chain ID (42161 for Arbitrum)
            
        Returns:
            Dictionary of token addresses to token info
        """
        try:
            url = f"{self.base_url}/swap/v5.2/{chain_id}/tokens"
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            data = response.json()
            return data.get("tokens", {})
            
        except Exception as e:
            print(f"❌ Error getting supported tokens: {e}")
            return {}
    
    def is_token_supported(self, token_symbol: str, chain_id: int = 42161) -> bool:
        """
        Check if a token is supported on 1inch
        
        Args:
            token_symbol: Token symbol (e.g., "USDC", "ETH")
            chain_id: Chain ID (42161 for Arbitrum)
            
        Returns:
            True if token is supported, False otherwise
        """
        tokens = self.get_supported_tokens(chain_id)
        
        # Search for token by symbol
        for token_address, token_info in tokens.items():
            if token_info.get("symbol", "").upper() == token_symbol.upper():
                return True
        
        return False
    
    def get_token_address(self, token_symbol: str, chain_id: int = 42161) -> Optional[str]:
        """
        Get token contract address by symbol
        
        Args:
            token_symbol: Token symbol (e.g., "USDC", "ETH")
            chain_id: Chain ID (42161 for Arbitrum)
            
        Returns:
            Token contract address or None if not found
        """
        tokens = self.get_supported_tokens(chain_id)
        
        # Search for token by symbol
        for token_address, token_info in tokens.items():
            if token_info.get("symbol", "").upper() == token_symbol.upper():
                return token_address
        
        return None
    
    def create_limit_order(self, 
                          from_token: str,
                          to_token: str,
                          amount: str,
                          price: str,
                          wallet_address: str,
                          chain_id: int = 42161) -> Optional[Dict]:
        """
        Create a limit order on 1inch
        
        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap (in wei)
            price: Price limit (in wei)
            wallet_address: Wallet address
            chain_id: Chain ID (42161 for Arbitrum)
            
        Returns:
            Order details or None if error
        """
        try:
            url = f"{self.base_url}/limit-order/v4.0/{chain_id}/order"
            
            payload = {
                "fromTokenAddress": from_token,
                "toTokenAddress": to_token,
                "amount": amount,
                "price": price,
                "walletAddress": wallet_address,
                "orderType": "fill_or_kill"  # or "post_only"
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error creating limit order: {e}")
            return None
    
    def get_quote(self, 
                  from_token: str,
                  to_token: str,
                  amount: str,
                  chain_id: int = 42161) -> Optional[Dict]:
        """
        Get quote for a swap
        
        Args:
            from_token: Source token address
            to_token: Destination token address
            amount: Amount to swap (in wei)
            chain_id: Chain ID (42161 for Arbitrum)
            
        Returns:
            Quote details or None if error
        """
        try:
            url = f"{self.base_url}/swap/v5.2/{chain_id}/quote"
            params = {
                "src": from_token,
                "dst": to_token,
                "amount": amount
            }
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            return response.json()
            
        except Exception as e:
            print(f"❌ Error getting quote: {e}")
            return None 


# Для обратной совместимости
if __name__ == "__main__":
    connector = OneInchConnector("WGq4QgUlaJDbU1TaYPRVJlNFnP4pq7KE")
    print(connector.is_token_supported("BTC"))
    