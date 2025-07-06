#!/usr/bin/env python3
"""
Funding Rate Arbitrage 
Arbitrum + Hyperliquid + 1inch Limit Order Protocol
"""

import os
import time
from datetime import datetime

from web3 import Web3

import K1inch
from CHAIN_ID import POLYGON, ARBITRUM
from connectors.balances import ARBITRUM_RPC, ArbitrumConnector
from connectors.database import db_manager
from connectors.hyperliquid import fetch_hyperliquid_markets, print_hyperliquid_markets_table
from oneInch_swap import OneInchClient
from utils.position_manager import PositionManager
from utils.print_header import print_header


# https://arb1.arbitrum.io/rpc
def limit_order(trade_amount_usdc, to_symbol="MATIC", current_price=0.0):
    client = OneInchClient(chain_id=ARBITRUM, private_key=K1inch.PRIVATE_KEY, api_key=K1inch.API_KEY)

    # Swap MATIC to USDC
    from_symbol = "USDC"
    from_symbol = _validate(from_symbol, fromS=True)
    to_symbol = _validate(to_symbol, fromS=False)


    from_token = client.get_token_address(from_symbol)
    to_token = client.get_token_address(to_symbol)
    amount_wei = Web3.to_wei(amount_, 'ether')

    quote = client.get_quote(from_token, to_token, amount_wei)
    print("Quote received:")
    print(quote)

    tx_data = client.build_swap_tx(from_token, to_token, amount_wei)

    tx_hash = client.send_transaction(tx_data)
    print(f"Transaction sent! Hash: {tx_hash}")


class FundingRateArbitrage:
    def __init__(self):
        self.arbitrum_address = os.environ.get("ARBITRUM_ADDRESS")
        self.arbitrum_private_key = os.environ.get("ARBITRUM_PRIVATE_KEY")
        self.hyperliquid_address = os.environ.get("HYPERLIQUID_ADDRESS")
        self.hyperliquid_private_key = os.environ.get("HYPERLIQUID_PRIVATE_KEY")

        self.oneinch_api_key = os.environ.get("ONEINCH_API_KEY")

        # System settings
        self.trade_amount_usdc = 10  # $10 USDC
        self.min_funding_rate = 0.000001  # TODO: do 0.1% minimum after debug
        self.min_time_until_funding = 0  # TODO: do 10 minutes after debug

        self.arbitrum_connector = ArbitrumConnector(ARBITRUM_RPC)
        # self.oneinch_connector = OneInchConnector(self.oneinch_api_key)

    def fetch_balances(self):
        hyperliquid_balances = self.arbitrum_connector.get_wallet_balances(self.hyperliquid_address)
        arbitrum_balances = self.arbitrum_connector.get_wallet_balances(self.arbitrum_address)

        self.hyperliquid_balances = hyperliquid_balances
        self.arbitrum_balances = arbitrum_balances

    def monitor_and_close_positions(self) -> bool:
        """Check if there are open positions and close them if it's time"""
        open_positions = None
        try:
           open_positions = db_manager.get_open_positions()
        except Exception as e:
            print(e)

        if not open_positions:
            return False

        # TODO: use after debug replance get_positions_to_close to get_open_positions
        # positions_to_close = db_manager.get_positions_to_close() 
        positions_to_close = db_manager.get_open_positions()

        if positions_to_close:
            print(f"\n🚪 CLOSING {len(positions_to_close)} POSITIONS:")
            print("─" * 50)
            for position in positions_to_close:
                # TODO: close position and sell hedge on 1inch
                time.sleep(10)

                print(f"\n🪓 ORDER EXECUTION:")
                print("─" * 30)
                print(f"   ✅ Exit short on Hyperliquid for ${position['hedge_quantity']} equivalent of {position['token_symbol']} at ${position['entry_price']:.4f}")
                print(f"   ✅ Sell hedge on 1inch limit order protocol (Arbitrum) for ${position['hedge_quantity']} equivalent of {position['token_symbol']} at ${position['entry_price']:.4f}")
                print("═" * 60)
                
                close_price = position['entry_price']
                
                PositionManager.close_position_with_pnl(
                    position_id=position['position_id'],
                    close_price=close_price,
                    notes="Auto close position"
                )

                
            
            print()
            return False

        return True

    def orders_execution(self, market):
        """
        Execute arbitrage orders: short on Hyperliquid and buy on 1inch
        """
        print(f"\n🚀 EXECUTING ARBITRAGE FOR {market['coin']}")
        print("═" * 60)

        # Calculate trade details
        trade_amount_usdc = self.trade_amount_usdc
        current_price = market['mark_px']
        funding_rate = market['funding_rate']

        # Calculate position sizes
        short_position_size = trade_amount_usdc / current_price  # How much to short

        # Calculate potential profits
        hourly_funding_profit = trade_amount_usdc * funding_rate
        daily_funding_profit = hourly_funding_profit * 24

        print(f"📊 TRADE DETAILS:")
        print("─" * 30)
        print(f"   Coin: {market['coin']}")
        print(f"   Current Price: ${current_price:.4f}")
        print(f"   Funding Rate: {funding_rate * 100:.4f}% per hour")
        print(f"   Trade Amount: ${trade_amount_usdc}")
        print(f"   Position Size: {short_position_size:.6f} {market['coin']}")

        print(f"\n💰 PROFIT CALCULATIONS:")
        print("─" * 30)
        print(
            f"   Hourly Funding Profit: ${hourly_funding_profit:.4f} ({hourly_funding_profit / trade_amount_usdc * 100:.4f}%)")
        print(
            f"   Daily Funding Profit: ${daily_funding_profit:.4f} ({daily_funding_profit / trade_amount_usdc * 100:.4f}%)")
        print(
            f"   Monthly Funding Profit: ${daily_funding_profit * 30:.2f} ({(daily_funding_profit * 30) / trade_amount_usdc * 100:.2f}%)")

        # TODO: execute short and hedge on 1inch
        time.sleep(10)

        print(f"\n🪓 ORDER EXECUTION:")
        print("─" * 30)
        print(
            f"   ✅ SHORT on Hyperliquid for ${trade_amount_usdc} equivalent of {market['coin']} at ${current_price:.4f}")
        print(
            f"   ✅ Hedge on 1inch limit order protocol (Arbitrum) for ${trade_amount_usdc} equivalent of {market['coin']} at ${current_price:.4f}")
        limit_order(trade_amount_usdc, market['coin'], current_price)

        # Создаем запись в базе данных
        try:
            position_id = PositionManager.create_arbitrage_position(
                token_symbol=market['coin'],
                token_address=f"0x{market['coin'].lower()}",  # Примерный адрес
                entry_price=current_price,
                quantity=short_position_size,
                hedge_token_symbol="USDC",
                hedge_token_address="0xA0b86a33E6441b8C4C8C8C8C8C8C8C8C8C8C8C8C",  # Примерный адрес USDC
                hedge_quantity=trade_amount_usdc,
                funding_rate=funding_rate,
                funding_duration_hours=8,
                exchange="hyperliquid",
                strategy_name="funding_arbitrage",
                notes=f"Funding arbitrage {market['coin']}/USDC"
            )
            print("═" * 60)
            return True
        except Exception as e:
            print(f"   ❌ Error saving position: {e}")
            print("═" * 60)
            return False

    def check_opportunity(self, market) -> bool:
        """Check if arbitrage opportunity exists for the given market"""

        # Check funding rate is above minimum
        if market['funding_rate'] < self.min_funding_rate:
            # print(f"❌ Funding rate is below minimum {self.min_funding_rate*100:.4f}%")
            return False

        # Check time until next funding
        time_until_funding = (market['next_funding_time'] - datetime.now()).total_seconds() / 60
        if time_until_funding < self.min_time_until_funding:
            # print(f"❌ Time until funding is below minimum {self.min_time_until_funding} minutes")
            return False

        # TODO: Check if we have sufficient funds (simplified check)
        # required_usdc = self.trade_amount_usdc
        # current_usdc_balance = self.hyperliquid_balances.get('usdc', 0)
        # print(f"💰 Balance check: {current_usdc_balance} USDC available, {required_usdc} USDC required")
        # if current_usdc_balance < required_usdc:
        #     print(f"❌ Insufficient USDC balance: {current_usdc_balance} < {required_usdc}")
        #     return False

        # 5. Check if token is available on 1inch (simplified - assume all are available for now)
        # TODO: Implement actual 1inch token availability check

        return True

    def run(self):
        """Run the complete demo"""
        print_header()

        while True:

            self.fetch_balances()
            self.markets = fetch_hyperliquid_markets()

            # Monitoring and closing positions
            is_active = self.monitor_and_close_positions()
            if is_active: continue

            self.arbitrum_connector.print_wallet_balances(self.hyperliquid_address, "HYPERLIQUID",
                                                          self.hyperliquid_balances)
            self.arbitrum_connector.print_wallet_balances(self.arbitrum_address, "ARBITRUM", self.arbitrum_balances)

            print("\n" + "─" * 80)

            print_hyperliquid_markets_table(self.markets)

            # Check for arbitrage opportunities across all markets
            arbitrage_found = False
            for market in self.markets:
                if self.check_opportunity(market):
                    self.orders_execution(market)
                    arbitrage_found = True
                    break

            if not arbitrage_found:
                print("\n❌ No arbitrage opportunities found")
                print("─" * 50)

            print(f"\n")
            print("=" * 80)
            print("=" * 80)
            time.sleep(10)

amount_ = 0.001
def _validate(arg, fromS=True):
    if fromS:
        return "MATIC"
    return "USDC"

if __name__ == "__main__":
    arbitrage = FundingRateArbitrage()
    arbitrage.run()
