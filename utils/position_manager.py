import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import logging
from connectors.database import db_manager

logger = logging.getLogger(__name__)

class PositionManager:
    """Менеджер для работы с торговыми позициями"""
    
    @staticmethod
    def generate_position_id() -> str:
        """Генерация уникального ID позиции"""
        return f"pos_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
    
    @staticmethod
    def create_arbitrage_position(
        token_symbol: str,
        token_address: str,
        entry_price: float,
        quantity: float,
        hedge_token_symbol: str,
        hedge_token_address: str,
        hedge_quantity: float,
        funding_rate: float,
        funding_duration_hours: int = 8,
        exchange: str = "hyperliquid",
        strategy_name: str = "funding_arbitrage",
        notes: str = ""
    ) -> str:
        """
        Создание позиции для арбитража фандинга
        
        Args:
            token_symbol: Символ основного токена
            token_address: Адрес основного токена
            entry_price: Цена входа
            quantity: Количество токенов в позиции
            hedge_token_symbol: Символ токена для хеджа
            hedge_token_address: Адрес токена для хеджа
            hedge_quantity: Количество токенов для хеджа
            funding_rate: Текущий фандинг рейт
            funding_duration_hours: Продолжительность фандинга в часах
            exchange: Биржа
            strategy_name: Название стратегии
            notes: Дополнительные заметки
        
        Returns:
            ID созданной позиции
        """
        position_id = PositionManager.generate_position_id()
        
        # Рассчитываем время окончания фандинга и закрытия позиции
        current_time = datetime.now()
        funding_end_time = current_time + timedelta(hours=funding_duration_hours)
        close_time = funding_end_time + timedelta(minutes=5)  # Закрываем через 5 минут после окончания фандинга
        
        position_data = {
            'position_id': position_id,
            'token_symbol': token_symbol,
            'token_address': token_address,
            'position_type': 'LONG',  # Для арбитража фандинга обычно лонг
            'entry_price': entry_price,
            'quantity': quantity,
            'hedge_quantity': hedge_quantity,
            'hedge_token_symbol': hedge_token_symbol,
            'hedge_token_address': hedge_token_address,
            'funding_rate': funding_rate,
            'funding_end_time': funding_end_time,
            'close_time': close_time,
            'exchange': exchange,
            'strategy_name': strategy_name,
            'notes': notes
        }
        
        try:
            db_manager.create_position(position_data)
            logger.info(f"Создана позиция арбитража: {position_id} для {token_symbol}")
            return position_id
        except Exception as e:
            # logger.error(f"Ошибка создания позиции: {e}")
            raise
    
    @staticmethod
    def get_positions_ready_to_close() -> List[Dict[str, Any]]:
        """Получение позиций, готовых к закрытию"""
        return db_manager.get_positions_to_close()
    
    @staticmethod
    def close_position_with_pnl(
        position_id: str,
        close_price: float,
        tx_hash: str = "",
        notes: str = ""
    ) -> bool:
        """
        Закрытие позиции с расчетом PnL
        
        Args:
            position_id: ID позиции
            close_price: Цена закрытия
            tx_hash: Хеш транзакции
            notes: Дополнительные заметки
        
        Returns:
            True если позиция успешно закрыта
        """
        position = db_manager.get_position_by_id(position_id)
        if not position:
            logger.error(f"Позиция {position_id} не найдена")
            return False
        
        # Рассчитываем PnL
        entry_price = position['entry_price']
        quantity = position['quantity']
        
        if position['position_type'] == 'LONG':
            pnl = (close_price - entry_price) * quantity
        else:  # SHORT
            pnl = (entry_price - close_price) * quantity
        
        # Вычитаем комиссии (примерно 0.1% за сделку)
        commission = abs(quantity * close_price * 0.001)
        pnl -= commission
        
        success = db_manager.close_position(position_id, close_price, pnl, tx_hash, notes)
        
        if success:
            logger.info(f"Позиция {position_id} закрыта. PnL: {pnl:.4f}, Цена закрытия: {close_price}")
        else:
            logger.error(f"Не удалось закрыть позицию {position_id}")
        
        return success
    
    @staticmethod
    def monitor_positions() -> Dict[str, Any]:
        """
        Мониторинг всех открытых позиций
        
        Returns:
            Словарь с информацией о позициях
        """
        open_positions = db_manager.get_open_positions()
        positions_to_close = db_manager.get_positions_to_close()
        
        # Рассчитываем общую статистику
        total_investment = sum(pos['entry_price'] * pos['quantity'] for pos in open_positions)
        total_hedge_value = sum(pos['entry_price'] * pos['hedge_quantity'] for pos in open_positions)
        
        return {
            'open_positions_count': len(open_positions),
            'positions_to_close_count': len(positions_to_close),
            'total_investment': total_investment,
            'total_hedge_value': total_hedge_value,
            'open_positions': open_positions,
            'positions_to_close': positions_to_close
        }
    
    @staticmethod
    def update_funding_rate(position_id: str, new_funding_rate: float) -> bool:
        """Обновление фандинг рейта для позиции"""
        return db_manager.update_position(position_id, {
            'funding_rate': new_funding_rate
        })
    
    @staticmethod
    def extend_position_time(position_id: str, additional_hours: int) -> bool:
        """Продление времени позиции"""
        position = db_manager.get_position_by_id(position_id)
        if not position:
            return False
        
        current_close_time = datetime.fromisoformat(position['close_time'])
        new_close_time = current_close_time + timedelta(hours=additional_hours)
        
        return db_manager.update_position(position_id, {
            'close_time': new_close_time
        })
    
    @staticmethod
    def get_position_summary(position_id: str) -> Optional[Dict[str, Any]]:
        """Получение сводки по позиции"""
        position = db_manager.get_position_by_id(position_id)
        if not position:
            return None
        
        history = db_manager.get_position_history(position_id)
        
        # Рассчитываем текущий PnL если позиция открыта
        current_pnl = None
        if position['status'] == 'OPEN':
            # Здесь можно добавить логику получения текущей цены
            # Пока возвращаем None
            pass
        
        return {
            'position': position,
            'history': history,
            'current_pnl': current_pnl,
            'time_until_close': None if position['status'] != 'OPEN' else 
                (datetime.fromisoformat(position['close_time']) - datetime.now()).total_seconds() / 3600
        }
    
    @staticmethod
    def get_trading_statistics() -> Dict[str, Any]:
        """Получение торговой статистики"""
        return db_manager.get_statistics()
    
    @staticmethod
    def cleanup_old_data(days: int = 30) -> int:
        """Очистка старых данных"""
        return db_manager.cleanup_old_positions(days)

# Пример использования
if __name__ == "__main__":
    # Пример создания позиции арбитража
    try:
        position_id = PositionManager.create_arbitrage_position(
            token_symbol="BTC",
            token_address="0x...",
            entry_price=45000.0,
            quantity=0.1,
            hedge_token_symbol="USDC",
            hedge_token_address="0x...",
            hedge_quantity=4500.0,
            funding_rate=0.0001,
            funding_duration_hours=8,
            notes="Арбитраж фандинга BTC/USDC"
        )
        print(f"Создана позиция: {position_id}")
        
        # Мониторинг позиций
        monitoring_data = PositionManager.monitor_positions()
        print(f"Открытых позиций: {monitoring_data['open_positions_count']}")
        print(f"Готовых к закрытию: {monitoring_data['positions_to_close_count']}")
        
    except Exception as e:
        print(f"Ошибка: {e}") 