#!/usr/bin/env python3
"""
Funding Rate Arbitrage 
Arbitrum + Hyperliquid + 1inch Limit Order Protocol
"""

import time
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import random
import os

from connectors.balances import ARBITRUM_RPC, ArbitrumConnector
from connectors.hyperliquid import fetch_hyperliquid_markets, print_hyperliquid_markets_table
from utils.print_header import print_header
# https://arb1.arbitrum.io/rpc
class FundingRateArbitrage:
    def __init__(self):
        self.arbitrum_address = os.environ.get("ARBITRUM_ADDRESS")
        self.arbitrum_private_key = os.environ.get("ARBITRUM_PRIVATE_KEY")
        self.hyperliquid_address = os.environ.get("HYPERLIQUID_ADDRESS")
        self.hyperliquid_private_key = os.environ.get("HYPERLIQUID_PRIVATE_KEY")
        self.oneinch_api_key = os.environ.get("1INCH_API_KEY")
        
        # System settings
        self.trade_amount_usdc = 10  # $10 USDC
        self.min_funding_rate = 0.00001   # 0.1% minimum funding rate for arbitrage
        
        self.arbitrum_connector = ArbitrumConnector(ARBITRUM_RPC)
        self.fetch_balances()

        # Get real Hyperliquid funding rates
        self.markets = fetch_hyperliquid_markets()
        
    def fetch_balances(self):
        hyperliquid_balances = self.arbitrum_connector.get_wallet_balances(self.hyperliquid_address)
        arbitrum_balances = self.arbitrum_connector.get_wallet_balances(self.arbitrum_address)
        
        self.hyperliquid_balances = hyperliquid_balances
        self.arbitrum_balances = arbitrum_balances
    
 

    def run(self):
        """Run the complete demo"""
        print_header()

        self.arbitrum_connector.print_wallet_balances(self.hyperliquid_address, "HYPERLIQUID", self.hyperliquid_balances)
        self.arbitrum_connector.print_wallet_balances(self.arbitrum_address, "ARBITRUM", self.arbitrum_balances)

        print_hyperliquid_markets_table(self.markets)
        
        if self.markets and self.markets[0]['funding_rate'] >= self.min_funding_rate:
            # Calculate potential hourly profit
            hourly_funding_rate = self.markets[0]['funding_rate']
            potential_hourly_profit = self.trade_amount_usdc * hourly_funding_rate
            
            print(f"✅ Found arbitrage opportunity: {self.markets[0]['coin']}")
            print(f"   Funding rate: {hourly_funding_rate*100:.4f}%")
            print(f"   Hourly profit: ${potential_hourly_profit:.4f}")
            print(f"   Trade amount: ${self.trade_amount_usdc}")
        else:
            print("❌ No arbitrage opportunities found")
            print()
       
        
        # if opportunity:
        #     self.print_arbitrage_execution(opportunity)
        #     self.print_8_hours_later(opportunity)
        # else:
        #     print("❌ No arbitrage opportunities found with current settings")
        #     print(f"   Minimum funding rate required: {self.min_funding_rate*100:.2f}%")
        #     print()

if __name__ == "__main__":
    arbitrage = FundingRateArbitrage()
    arbitrage.run()
