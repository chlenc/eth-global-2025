import sqlite3
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Use path in Docker container
            db_path = os.path.join("/app/data", "trading_positions.db")
        self.db_path = db_path
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_database()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_database(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Create table for open positions
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS open_positions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id TEXT UNIQUE NOT NULL,
                    token_symbol TEXT NOT NULL,
                    token_address TEXT NOT NULL,
                    position_type TEXT NOT NULL CHECK (position_type IN ('LONG', 'SHORT')),
                    entry_price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    hedge_quantity REAL NOT NULL,
                    hedge_token_symbol TEXT NOT NULL,
                    hedge_token_address TEXT NOT NULL,
                    funding_rate REAL NOT NULL,
                    funding_end_time TIMESTAMP NOT NULL,
                    close_time TIMESTAMP NOT NULL,
                    status TEXT NOT NULL DEFAULT 'OPEN' CHECK (status IN ('OPEN', 'CLOSED', 'CANCELLED')),
                    pnl REAL DEFAULT 0.0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    exchange TEXT NOT NULL,
                    strategy_name TEXT NOT NULL,
                    notes TEXT
                )
            ''')
            
            # Create indexes for fast search
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_position_status ON open_positions(status)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_funding_end_time ON open_positions(funding_end_time)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_close_time ON open_positions(close_time)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_token_symbol ON open_positions(token_symbol)
            ''')
            
            # Create table for operation history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS position_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    position_id TEXT NOT NULL,
                    action TEXT NOT NULL CHECK (action IN ('OPEN', 'CLOSE', 'UPDATE', 'HEDGE')),
                    price REAL,
                    quantity REAL,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    tx_hash TEXT,
                    gas_used REAL,
                    gas_price REAL,
                    notes TEXT,
                    FOREIGN KEY (position_id) REFERENCES open_positions(position_id)
                )
            ''')
            
            conn.commit()
            logger.info("Database initialized successfully")
    
    def create_position(self, position_data: Dict[str, Any]) -> str:
        """Create new open position"""
        required_fields = [
            'position_id', 'token_symbol', 'token_address', 'position_type',
            'entry_price', 'quantity', 'hedge_quantity', 'hedge_token_symbol',
            'hedge_token_address', 'funding_rate', 'funding_end_time',
            'close_time', 'exchange', 'strategy_name'
        ]
        
        for field in required_fields:
            if field not in position_data:
                raise ValueError(f"Missing required field: {field}")
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO open_positions (
                    position_id, token_symbol, token_address, position_type,
                    entry_price, quantity, hedge_quantity, hedge_token_symbol,
                    hedge_token_address, funding_rate, funding_end_time,
                    close_time, exchange, strategy_name, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                position_data['position_id'],
                position_data['token_symbol'],
                position_data['token_address'],
                position_data['position_type'],
                position_data['entry_price'],
                position_data['quantity'],
                position_data['hedge_quantity'],
                position_data['hedge_token_symbol'],
                position_data['hedge_token_address'],
                position_data['funding_rate'],
                position_data['funding_end_time'],
                position_data['close_time'],
                position_data['exchange'],
                position_data['strategy_name'],
                position_data.get('notes', '')
            ))
            
            # Write opening action to history
            cursor.execute('''
                INSERT INTO position_history (
                    position_id, action, price, quantity, tx_hash, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                position_data['position_id'],
                'OPEN',
                position_data['entry_price'],
                position_data['quantity'],
                position_data.get('tx_hash', ''),
                'Position opened'
            ))
            
            conn.commit()
            logger.info(f"Position {position_data['position_id']} created successfully")
            return position_data['position_id']
    
    def close_position(self, position_id: str, close_price: float, 
                      pnl: float, tx_hash: str = '', notes: str = '') -> bool:
        """Close position"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Update position status
            cursor.execute('''
                UPDATE open_positions 
                SET status = 'CLOSED', pnl = ?, updated_at = CURRENT_TIMESTAMP
                WHERE position_id = ? AND status = 'OPEN'
            ''', (pnl, position_id))
            
            if cursor.rowcount == 0:
                logger.warning(f"Position {position_id} not found or already closed")
                return False
            
            # Write closing action to history
            cursor.execute('''
                INSERT INTO position_history (
                    position_id, action, price, quantity, tx_hash, notes
                ) VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                position_id,
                'CLOSE',
                close_price,
                0,  # quantity when closing
                tx_hash,
                notes or 'Position closed'
            ))
            
            conn.commit()
            logger.info(f"Position {position_id} closed successfully, PnL: {pnl}")
            return True
    
    def get_open_positions(self) -> List[Dict[str, Any]]:
        """Get all open positions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM open_positions WHERE status = 'OPEN'
                ORDER BY created_at DESC
            ''')
            
            columns = [description[0] for description in cursor.description]
            positions = []
            
            for row in cursor.fetchall():
                position = dict(zip(columns, row))
                positions.append(position)
            
            return positions
    
    def get_positions_to_close(self, current_time: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """Get positions that need to be closed"""
        if current_time is None:
            current_time = datetime.now()
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM open_positions 
                WHERE status = 'OPEN' AND close_time <= ?
                ORDER BY close_time ASC
            ''', (current_time,))
            
            columns = [description[0] for description in cursor.description]
            positions = []
            
            for row in cursor.fetchall():
                position = dict(zip(columns, row))
                positions.append(position)
            
            return positions
    
    def get_position_by_id(self, position_id: str) -> Optional[Dict[str, Any]]:
        """Get position by ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM open_positions WHERE position_id = ?
            ''', (position_id,))
            
            row = cursor.fetchone()
            if row:
                columns = [description[0] for description in cursor.description]
                return dict(zip(columns, row))
            return None
    
    def update_position(self, position_id: str, updates: Dict[str, Any]) -> bool:
        """Update position"""
        allowed_fields = [
            'entry_price', 'quantity', 'hedge_quantity', 'funding_rate',
            'funding_end_time', 'close_time', 'notes'
        ]
        
        update_fields = []
        values = []
        
        for field, value in updates.items():
            if field in allowed_fields:
                update_fields.append(f"{field} = ?")
                values.append(value)
        
        if not update_fields:
            return False
        
        update_fields.append("updated_at = CURRENT_TIMESTAMP")
        values.append(position_id)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f'''
                UPDATE open_positions 
                SET {', '.join(update_fields)}
                WHERE position_id = ?
            ''', values)
            
            if cursor.rowcount > 0:
                # Записываем обновление в историю
                cursor.execute('''
                    INSERT INTO position_history (
                        position_id, action, notes
                    ) VALUES (?, ?, ?)
                ''', (
                    position_id,
                    'UPDATE',
                    f"Позиция обновлена: {', '.join(updates.keys())}"
                ))
                
                conn.commit()
                logger.info(f"Позиция {position_id} обновлена")
                return True
            
            return False
    
    def get_position_history(self, position_id: str) -> List[Dict[str, Any]]:
        """Get position history"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT * FROM position_history 
                WHERE position_id = ?
                ORDER BY timestamp DESC
            ''', (position_id,))
            
            columns = [description[0] for description in cursor.description]
            history = []
            
            for row in cursor.fetchall():
                entry = dict(zip(columns, row))
                history.append(entry)
            
            return history
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics by positions"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Общая статистика
            cursor.execute('''
                SELECT 
                    COUNT(*) as total_positions,
                    COUNT(CASE WHEN status = 'OPEN' THEN 1 END) as open_positions,
                    COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) as closed_positions,
                    SUM(CASE WHEN status = 'CLOSED' THEN pnl ELSE 0 END) as total_pnl,
                    AVG(CASE WHEN status = 'CLOSED' THEN pnl ELSE NULL END) as avg_pnl
                FROM open_positions
            ''')
            
            stats = cursor.fetchone()
            
            # Статистика по токенам
            cursor.execute('''
                SELECT 
                    token_symbol,
                    COUNT(*) as position_count,
                    SUM(CASE WHEN status = 'CLOSED' THEN pnl ELSE 0 END) as total_pnl
                FROM open_positions
                GROUP BY token_symbol
                ORDER BY total_pnl DESC
            ''')
            
            token_stats = cursor.fetchall()
            
            return {
                'total_positions': stats[0],
                'open_positions': stats[1],
                'closed_positions': stats[2],
                'total_pnl': stats[3] or 0,
                'avg_pnl': stats[4] or 0,
                'token_statistics': [
                    {
                        'token_symbol': row[0],
                        'position_count': row[1],
                        'total_pnl': row[2] or 0
                    }
                    for row in token_stats
                ]
            }
    
    def cleanup_old_positions(self, days: int = 30) -> int:
        """Cleanup old closed positions"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Delete old records from history
            cursor.execute('''
                DELETE FROM position_history 
                WHERE position_id IN (
                    SELECT position_id FROM open_positions 
                    WHERE status = 'CLOSED' AND updated_at < ?
                )
            ''', (cutoff_date,))
            
            history_deleted = cursor.rowcount
            
            # Delete old closed positions
            cursor.execute('''
                DELETE FROM open_positions 
                WHERE status = 'CLOSED' AND updated_at < ?
            ''', (cutoff_date,))
            
            positions_deleted = cursor.rowcount
            
            conn.commit()
            logger.info(f"Удалено {positions_deleted} позиций и {history_deleted} записей истории")
            return positions_deleted
db_manager = None
# Create global instance of database manager
try:

   db_manager = DatabaseManager()
except Exception as e:
    print(e)