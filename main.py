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

from connectors.hliq import get_current_funding, sort_by_value_desc
from connectors.hyperliquid import fetch_hyperliquid_markets, print_hyperliquid_markets_table
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
        self.min_funding_rate = 0.000015   # 0.1% minimum funding rate for arbitrage
        
        # TODO get Balances from 
        self.balances = {
            "arbitrum": {
                "usdc": 89.21,
                "eth": 0.521
            },
            "hyperliquid": {
                "usdc": 114.1434,
            }
        }
        
        # Get real Hyperliquid funding rates
        self.hyperliquid_funding_rates = self.get_real_funding_rates()
        
    
        # Current prices (fake)
        self.prices = {
            "BTC": 43250.0,
            "ETH": 2650.0,
            "SOL": 98.5,
            "MATIC": 0.85,
            "AVAX": 35.2,
            "LINK": 15.8,
            "UNI": 7.2,
            "AAVE": 95.0
        }

    def get_real_funding_rates(self) -> List[Dict]:
        """Get real funding rates from Hyperliquid API"""
        print("🔍 Fetching real funding rates from Hyperliquid...")
        
        # Get current funding data using new function
        markets = fetch_hyperliquid_markets()
        
        # Convert to the format expected by the rest of the code
        funding_rates = []
        for market in markets:
            funding_rates.append({
                "symbol": market["coin"],
                "funding_rate": market["funding_rate"],
                "next_funding": market["next_funding_time"].isoformat(" ") if market["next_funding_time"] else "N/A",
                "volume_24h": market["volume_24h_usd"],
                "price": market["mark_px"]
            })
        
        print(f"✅ Fetched {len(funding_rates)} funding rates from Hyperliquid")
        return funding_rates

    def print_header(self):
        """Print styled header"""
        print("=" * 80)
        print("🚀 FUNDING RATE ARBITRAGE BOT")
        print("   Arbitrum + Hyperliquid + 1inch Limit Order Protocol")
        print("=" * 80)
        print()

    def print_section(self, title: str):
        """Print section header"""
        print(f"\n{'='*20} {title} {'='*20}")
        print()

    def print_wallet_login(self):
        """Simulate wallet login and show balances"""
        self.print_section("WALLET LOGIN & BALANCES")
        
        print("🔐 Connecting to Arbitrum...")
        time.sleep(0.5)
        print(f"✅ Connected! Wallet: {self.wallet_address}")
        print()
        
        print("🔐 Connecting to Hyperliquid...")
        time.sleep(0.5)
        print(f"✅ Connected! Wallet: {self.wallet_address}")
        print()
        
        print("💰 BALANCES:")
        print("   Arbitrum:")
        print(f"     USDC: ${self.balances['arbitrum']['usdc']:,.2f}")
        print(f"     ETH:  {self.balances['arbitrum']['eth']:.4f}")
        print()
        print("   Hyperliquid:")
        print(f"     USDC: ${self.balances['hyperliquid']['usdc']:,.2f}")
        print()
        
        print("⚙️  SYSTEM SETTINGS:")
        print(f"   Trade Amount: ${self.trade_amount_usdc:,.2f} USDC")
        print(f"   Min Funding Rate: {self.min_funding_rate*100:.2f}%")
        print()

    def print_funding_rates(self):
        """Print sorted funding rates from Hyperliquid"""
        self.print_section("HYPERLIQUID FUNDING RATES")
        
        # Use the new beautiful table function
        print_hyperliquid_markets_table()

    def check_arbitrage_opportunity(self) -> Optional[Dict]:
        """Check for arbitrage opportunities"""
        for rate in self.hyperliquid_funding_rates:
            if rate['funding_rate'] >= self.min_funding_rate:
                # Update price from real data
                if 'price' in rate:
                    self.prices[rate['symbol']] = rate['price']
                return rate
        return None

    def print_arbitrage_execution(self, opportunity: Dict):
        """Print arbitrage execution steps"""
        self.print_section("ARBITRAGE EXECUTION")
        
        symbol = opportunity['symbol']
        funding_rate = opportunity['funding_rate']
        price = self.prices[symbol]
        amount_tokens = self.trade_amount_usdc / price
        
        print(f"🎯 ARBITRAGE OPPORTUNITY FOUND!")
        print(f"   Token: {symbol}")
        print(f"   Funding Rate: {funding_rate*100:.4f}%")
        print(f"   Price: ${price:,.2f}")
        print(f"   Trade Amount: {amount_tokens:.6f} {symbol} (${self.trade_amount_usdc:,.2f})")
        print()
        
        # Step 1: Open short on Hyperliquid
        print("📉 STEP 1: Opening Short Position on Hyperliquid")
        print("   Transaction Hash: 0x8f7a3b2c1d9e4f5a6b7c8d9e0f1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b")
        print(f"   Action: SHORT {amount_tokens:.6f} {symbol}")
        print(f"   Entry Price: ${price:,.2f}")
        print(f"   Collateral: ${self.trade_amount_usdc:,.2f} USDC")
        print(f"   Expected Funding: ${self.trade_amount_usdc * funding_rate * 8:,.2f} (8h)")
        print()
        
        # Step 2: Hedge on 1inch
        print("🛡️  STEP 2: Hedging on 1inch Limit Order Protocol")
        print("   Transaction Hash: 0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c")
        print(f"   Action: BUY {amount_tokens:.6f} {symbol}")
        print(f"   Limit Price: ${price * 0.999:,.2f} (0.1% below market)")
        print(f"   Order Type: Limit Order")
        print(f"   Expiration: 8 hours")
        print()

    def print_8_hours_later(self, opportunity: Dict):
        """Print 8 hours later scenario"""
        self.print_section("8 HOURS LATER")
        
        symbol = opportunity['symbol']
        funding_rate = opportunity['funding_rate']
        price = self.prices[symbol]
        amount_tokens = self.trade_amount_usdc / price
        
        # Simulate price change
        price_change = random.uniform(-0.02, 0.02)  # ±2%
        new_price = price * (1 + price_change)
        
        
        # Step 3: Close short on Hyperliquid
        print("📈 STEP 3: Closing Short Position on Hyperliquid")
        print("   Transaction Hash: 0x9b8a7c6d5e4f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9c8d7e6f5a4b3c2d1e0f9a8b")
        print(f"   Action: CLOSE SHORT {amount_tokens:.6f} {symbol}")
        print(f"   Exit Price: ${new_price:,.2f}")
        print(f"   P&L from price: ${self.trade_amount_usdc * price_change:,.2f}")
        print()
        
        # Step 4: Sell on 1inch
        print("💰 STEP 4: Selling on 1inch Limit Order Protocol")
        print("   Transaction Hash: 0x2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b1c2d3e4f5a6b7c8d9e0f1a2b3c4d")
        print(f"   Action: SELL {amount_tokens:.6f} {symbol}")
        print(f"   Limit Price: ${new_price * 1.001:,.2f} (0.1% above market)")
        print(f"   Order Type: Limit Order")
        print()
        
        # Calculate total profit
        funding_profit = self.trade_amount_usdc * funding_rate * 8
        price_pnl = self.trade_amount_usdc * price_change
        total_profit = funding_profit + price_pnl
        
        print("📊 ARBITRAGE RESULTS:")
        print(f"   Funding Profit: ${funding_profit:,.2f}")
        print(f"   Price P&L: ${price_pnl:,.2f}")
        print(f"   Total Profit: ${total_profit:,.2f}")
        print(f"   ROI: {(total_profit/self.trade_amount_usdc)*100:.4f}%")
        print()

    def run_demo(self):
        """Run the complete demo"""
        self.print_header()
        self.print_wallet_login()
        self.print_funding_rates()
        
        # Check for arbitrage opportunity
        opportunity = self.check_arbitrage_opportunity()
        
        if opportunity:
            self.print_arbitrage_execution(opportunity)
            self.print_8_hours_later(opportunity)
        else:
            print("❌ No arbitrage opportunities found with current settings")
            print(f"   Minimum funding rate required: {self.min_funding_rate*100:.2f}%")
            print()

if __name__ == "__main__":
    arbitrage = FundingRateArbitrage()
    arbitrage.run_demo()
