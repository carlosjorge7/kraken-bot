"""
Database Manager - Gestión de persistencia en SQLite
"""

import sqlite3
import pandas as pd
from typing import Optional
import logging
from pathlib import Path


class DatabaseManager:
    """Gestor de base de datos SQLite para almacenar datos OHLCV."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Crear directorio si no existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        self._create_tables()
    
    def _create_tables(self):
        """Crea las tablas necesarias."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ohlcv (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME NOT NULL,
                symbol TEXT NOT NULL,
                open REAL NOT NULL,
                high REAL NOT NULL,
                low REAL NOT NULL,
                close REAL NOT NULL,
                volume REAL NOT NULL,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(timestamp, symbol)
            )
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON ohlcv(symbol, timestamp DESC)
        """)
        
        conn.commit()
        conn.close()
        self.logger.info(f"Base de datos inicializada: {self.db_path}")
    
    def save_ohlcv(self, df: pd.DataFrame) -> int:
        """
        Guarda datos OHLCV evitando duplicados.
        
        Returns:
            Número de filas insertadas
        """
        if df.empty:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        inserted = 0
        
        try:
            for _, row in df.iterrows():
                try:
                    # Convertir timestamp a string ISO
                    timestamp_str = row['timestamp'].isoformat() if hasattr(row['timestamp'], 'isoformat') else str(row['timestamp'])
                    
                    conn.execute("""
                        INSERT OR IGNORE INTO ohlcv 
                        (timestamp, symbol, open, high, low, close, volume)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        timestamp_str,
                        str(row['symbol']),
                        float(row['open']),
                        float(row['high']),
                        float(row['low']),
                        float(row['close']),
                        float(row['volume'])
                    ))
                    if conn.total_changes > 0:
                        inserted += 1
                except sqlite3.IntegrityError:
                    continue
            
            conn.commit()
            self.logger.info(f"Guardadas {inserted} nuevas velas en BD")
            
        finally:
            conn.close()
        
        return inserted
    
    def get_latest(self, symbol: str, limit: int = 100) -> pd.DataFrame:
        """Obtiene las últimas velas de un símbolo."""
        conn = sqlite3.connect(self.db_path)
        
        query = """
            SELECT timestamp, symbol, open, high, low, close, volume
            FROM ohlcv
            WHERE symbol = ?
            ORDER BY timestamp DESC
            LIMIT ?
        """
        
        df = pd.read_sql_query(query, conn, params=[symbol, limit])
        conn.close()
        
        if not df.empty:
            df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        return df
    
    def count_records(self, symbol: Optional[str] = None) -> int:
        """Cuenta registros totales o por símbolo."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if symbol:
            cursor.execute("SELECT COUNT(*) FROM ohlcv WHERE symbol = ?", (symbol,))
        else:
            cursor.execute("SELECT COUNT(*) FROM ohlcv")
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
