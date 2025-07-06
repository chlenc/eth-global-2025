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
import requests

from connectors.balances import ARBITRUM_RPC, ArbitrumConnector
from connectors.hyperliquid import fetch_hyperliquid_markets, print_hyperliquid_markets_table
from utils.print_header import print_header
from utils.position_manager import PositionManager
from connectors.database import db_manager
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
        self.min_time_until_funding = 0 # 10 minutes
        
        self.arbitrum_connector = ArbitrumConnector(ARBITRUM_RPC)
        # self.oneinch_connector = OneInchConnector(self.oneinch_api_key)

        
    def fetch_balances(self):
        hyperliquid_balances = self.arbitrum_connector.get_wallet_balances(self.hyperliquid_address)
        arbitrum_balances = self.arbitrum_connector.get_wallet_balances(self.arbitrum_address)
        
        self.hyperliquid_balances = hyperliquid_balances
        self.arbitrum_balances = arbitrum_balances
    
    def monitor_and_close_positions(self):
        """Мониторинг и закрытие позиций"""
        print(f"\n🔍 MONITORING POSITIONS")
        print("=" * 60)
        
        # Получаем данные мониторинга
        monitoring_data = PositionManager.monitor_positions()
        
        print(f"📊 POSITION SUMMARY:")
        print(f"   Открытых позиций: {monitoring_data['open_positions_count']}")
        print(f"   Готовых к закрытию: {monitoring_data['positions_to_close_count']}")
        print(f"   Общая инвестиция: ${monitoring_data['total_investment']:.2f}")
        print(f"   Общий хедж: ${monitoring_data['total_hedge_value']:.2f}")
        
        # Закрываем позиции, готовые к закрытию
        if monitoring_data['positions_to_close']:
            print(f"\n🚪 CLOSING POSITIONS:")
            for position in monitoring_data['positions_to_close']:
                print(f"   Закрытие позиции {position['position_id']} для {position['token_symbol']}")
                
                # Здесь можно добавить логику получения текущей цены
                # Пока используем цену входа как пример
                close_price = position['entry_price']
                
                success = PositionManager.close_position_with_pnl(
                    position_id=position['position_id'],
                    close_price=close_price,
                    notes="Автоматическое закрытие по времени"
                )
                
                if success:
                    print(f"   ✅ Позиция {position['position_id']} закрыта успешно")
                else:
                    print(f"   ❌ Ошибка закрытия позиции {position['position_id']}")
        else:
            print(f"   ✅ Нет позиций для закрытия")
        
        # Показываем статистику
        stats = PositionManager.get_trading_statistics()
        print(f"\n📈 TRADING STATISTICS:")
        print(f"   Всего позиций: {stats['total_positions']}")
        print(f"   Закрытых позиций: {stats['closed_positions']}")
        print(f"   Общий PnL: ${stats['total_pnl']:.4f}")
        print(f"   Средний PnL: ${stats['avg_pnl']:.4f}")
        
        if stats['token_statistics']:
            print(f"   📊 По токенам:")
            for token_stat in stats['token_statistics'][:3]:  # Показываем топ-3
                print(f"      {token_stat['token_symbol']}: {token_stat['position_count']} позиций, PnL: ${token_stat['total_pnl']:.4f}")


    def orders_execution(self, market):
        """
        Execute arbitrage orders: short on Hyperliquid and buy on 1inch
        """
        print(f"\n🚀 EXECUTING ARBITRAGE FOR {market['coin']}")
        print("=" * 60)
        
        # Calculate trade details
        trade_amount_usdc = self.trade_amount_usdc
        current_price = market['mark_px']
        funding_rate = market['funding_rate']
        
        # Calculate position sizes
        short_position_size = trade_amount_usdc / current_price  # How much to short
        long_position_size = trade_amount_usdc / current_price   # How much to buy
        
        # Calculate potential profits
        hourly_funding_profit = trade_amount_usdc * funding_rate
        daily_funding_profit = hourly_funding_profit * 24
        
        print(f"📊 TRADE DETAILS:")
        print(f"   Coin: {market['coin']}")
        print(f"   Current Price: ${current_price:.4f}")
        print(f"   Funding Rate: {funding_rate*100:.4f}% per hour")
        print(f"   Trade Amount: ${trade_amount_usdc}")
        print(f"   Position Size: {short_position_size:.6f} {market['coin']}")
        
        print(f"\n💰 PROFIT CALCULATIONS:")
        print(f"   Hourly Funding Profit: ${hourly_funding_profit:.4f} ({hourly_funding_profit/trade_amount_usdc*100:.4f}%)")
        print(f"   Daily Funding Profit: ${daily_funding_profit:.4f} ({daily_funding_profit/trade_amount_usdc*100:.4f}%)")
        print(f"   Monthly Funding Profit: ${daily_funding_profit * 30:.2f} ({(daily_funding_profit * 30)/trade_amount_usdc*100:.2f}%)")
        
        print(f"\n📋 ORDER EXECUTION:")
        print(f"   🔻 SHORT on Hyperliquid:")
        print(f"      Executed SHORT order for ${trade_amount_usdc} equivalent of {market['coin']} at ${current_price:.4f}")
        
        print(f"   🔐 Hedge on 1inch limit order protocol (Arbitrum):")
        print(f"      Executed BUY order for ${trade_amount_usdc} equivalent of {market['coin']} at ${current_price:.4f}")

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
                notes=f"Арбитраж фандинга {market['coin']}/USDC"
            )
            print(f"   💾 Позиция сохранена в БД: {position_id}")
            return True
        except Exception as e:
            print(f"   ❌ Ошибка сохранения позиции: {e}")
            return False

    def check_opportunity(self, market) -> bool:
        """Check if arbitrage opportunity exists for the given market"""
        
        # 1. Check funding rate is above minimum
        if market['funding_rate'] < self.min_funding_rate: 
            print(f"❌ Funding rate is below minimum {self.min_funding_rate*100:.2f}%")
            return False
        
        # 2. Check time until next funding
        time_until_funding = (market['next_funding_time'] - datetime.now()).total_seconds() / 60
        if time_until_funding < self.min_time_until_funding:
            print(f"❌ Time until funding is below minimum {self.min_time_until_funding} minutes")
            return False
        
        # 3. Check if position is already open
        # 4. Check if we have sufficient funds
        # 5. Check if token is available on 1inch
                

    def run(self):
        """Run the complete demo"""
        print_header()

        # todo LOOP

        self.fetch_balances()
        self.markets = fetch_hyperliquid_markets()

        self.arbitrum_connector.print_wallet_balances(self.hyperliquid_address, "HYPERLIQUID", self.hyperliquid_balances)
        self.arbitrum_connector.print_wallet_balances(self.arbitrum_address, "ARBITRUM", self.arbitrum_balances)

          # Мониторинг и закрытие позиций
        self.monitor_and_close_positions()

        print_hyperliquid_markets_table(self.markets)
        
        # Check for arbitrage opportunities
        if self.markets and self.check_opportunity(self.markets[0]):
            self.orders_execution(self.markets[0])
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
