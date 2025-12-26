"""
Prediction Backtester - Sistema de Evaluación de Predicciones

Registra predicciones y evalúa su accuracy direccional comparando
contra el movimiento real del precio.

NO simula trading, solo mide accuracy direccional.
"""

import logging
import json
import sqlite3
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import pandas as pd


class Direction(str, Enum):
    """Direcciones de predicción"""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


class Horizon(str, Enum):
    """Horizontes temporales"""
    NEXT_1_CANDLE = "next_1_candle"
    NEXT_3_CANDLES = "next_3_candles"
    NEXT_5_CANDLES = "next_5_candles"


@dataclass
class PredictionRecord:
    """Registro de una predicción para backtesting"""
    id: Optional[int] = None
    symbol: str = ""
    timeframe: str = ""
    direction_predicted: str = ""
    confidence: float = 0.0
    quality: str = ""
    horizon: str = ""
    timestamp_predicted: str = ""
    price_at_prediction: float = 0.0
    
    # Campos de verificación (se llenan después)
    price_after_1_candle: Optional[float] = None
    price_after_3_candles: Optional[float] = None
    price_after_5_candles: Optional[float] = None
    actual_direction_1c: Optional[str] = None
    actual_direction_3c: Optional[str] = None
    actual_direction_5c: Optional[str] = None
    is_correct_1c: Optional[bool] = None
    is_correct_3c: Optional[bool] = None
    is_correct_5c: Optional[bool] = None
    timestamp_verified: Optional[str] = None


@dataclass
class BacktestResult:
    """Resultado de backtesting"""
    total_predictions: int
    accuracy_1c: float
    accuracy_3c: float
    accuracy_5c: float
    accuracy_by_confidence: Dict[str, float]
    accuracy_by_quality: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]
    timestamp: str


class PredictionBacktester:
    """
    Sistema de backtesting para predicciones direccionales.
    
    Funciones:
    1. Registrar predicciones en el momento que se generan
    2. Verificar resultados cuando hay datos disponibles
    3. Calcular métricas de accuracy
    """
    
    def __init__(self, db_path: str = "data/backtesting.db", json_path: str = "data/backtesting.json"):
        """
        Inicializa el backtester.
        
        Args:
            db_path: Ruta a la base de datos SQLite
            json_path: Ruta al archivo JSON de respaldo
        """
        self.logger = logging.getLogger(__name__)
        self.db_path = db_path
        self.json_path = json_path
        
        # Crear estructura de datos
        self._ensure_storage()
    
    def _ensure_storage(self):
        """Crea las estructuras de almacenamiento necesarias"""
        # Crear directorio
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        Path(self.json_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Crear tabla en SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timeframe TEXT NOT NULL,
                direction_predicted TEXT NOT NULL,
                confidence REAL NOT NULL,
                quality TEXT NOT NULL,
                horizon TEXT NOT NULL,
                timestamp_predicted TEXT NOT NULL,
                price_at_prediction REAL NOT NULL,
                
                price_after_1_candle REAL,
                price_after_3_candles REAL,
                price_after_5_candles REAL,
                actual_direction_1c TEXT,
                actual_direction_3c TEXT,
                actual_direction_5c TEXT,
                is_correct_1c INTEGER,
                is_correct_3c INTEGER,
                is_correct_5c INTEGER,
                timestamp_verified TEXT,
                
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Índices para búsquedas rápidas
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_symbol_timestamp 
            ON predictions(symbol, timestamp_predicted)
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_verified 
            ON predictions(timestamp_verified)
        """)
        
        conn.commit()
        conn.close()
        
        # Crear archivo JSON si no existe
        if not Path(self.json_path).exists():
            self._write_json({"predictions": [], "last_update": None})
    
    def _write_json(self, data: Dict[str, Any]):
        """Escribe datos al archivo JSON"""
        with open(self.json_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _read_json(self) -> Dict[str, Any]:
        """Lee datos del archivo JSON"""
        try:
            with open(self.json_path, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {"predictions": [], "last_update": None}
    
    def record_prediction(
        self,
        symbol: str,
        timeframe: str,
        direction: str,
        confidence: float,
        quality: str,
        horizon: str,
        price: float
    ) -> int:
        """
        Registra una nueva predicción.
        
        Args:
            symbol: Símbolo del mercado
            timeframe: Timeframe usado
            direction: Dirección predicha (UP/DOWN/NEUTRAL)
            confidence: Nivel de confianza (0-1)
            quality: Calidad de la predicción (HIGH/MEDIUM/LOW)
            horizon: Horizonte temporal
            price: Precio en el momento de la predicción
        
        Returns:
            ID del registro creado
        """
        record = PredictionRecord(
            symbol=symbol,
            timeframe=timeframe,
            direction_predicted=direction,
            confidence=confidence,
            quality=quality,
            horizon=horizon,
            timestamp_predicted=datetime.now().isoformat(),
            price_at_prediction=price
        )
        
        # Guardar en SQLite
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            INSERT INTO predictions (
                symbol, timeframe, direction_predicted, confidence, quality,
                horizon, timestamp_predicted, price_at_prediction
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            record.symbol,
            record.timeframe,
            record.direction_predicted,
            record.confidence,
            record.quality,
            record.horizon,
            record.timestamp_predicted,
            record.price_at_prediction
        ))
        
        record_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        self.logger.debug(f"Predicción registrada: {symbol} {direction} @ {confidence:.2%} (ID: {record_id})")
        
        return record_id
    
    def verify_predictions(self, symbol: str, current_df: pd.DataFrame) -> int:
        """
        Verifica predicciones pendientes comparando contra datos reales.
        
        Args:
            symbol: Símbolo a verificar
            current_df: DataFrame con datos OHLCV actuales
        
        Returns:
            Número de predicciones verificadas
        """
        if current_df.empty:
            return 0
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener predicciones sin verificar para este símbolo
        cursor.execute("""
            SELECT id, timestamp_predicted, price_at_prediction, 
                   direction_predicted, horizon
            FROM predictions
            WHERE symbol = ? AND timestamp_verified IS NULL
            ORDER BY timestamp_predicted ASC
        """, (symbol,))
        
        pending = cursor.fetchall()
        verified_count = 0
        
        for pred_id, ts_pred, price_pred, direction_pred, horizon in pending:
            # Convertir timestamp a datetime
            dt_pred = datetime.fromisoformat(ts_pred)
            
            # Buscar precios futuros en el DataFrame
            # Filtrar datos posteriores a la predicción
            future_data = current_df[current_df['timestamp'] > dt_pred].copy()
            
            if len(future_data) == 0:
                continue  # No hay datos suficientes todavía
            
            # Obtener precios en los horizontes especificados
            price_1c = future_data.iloc[0]['close'] if len(future_data) >= 1 else None
            price_3c = future_data.iloc[2]['close'] if len(future_data) >= 3 else None
            price_5c = future_data.iloc[4]['close'] if len(future_data) >= 5 else None
            
            # Calcular direcciones reales
            actual_1c = self._calculate_direction(price_pred, price_1c) if price_1c else None
            actual_3c = self._calculate_direction(price_pred, price_3c) if price_3c else None
            actual_5c = self._calculate_direction(price_pred, price_5c) if price_5c else None
            
            # Verificar aciertos
            is_correct_1c = (actual_1c == direction_pred) if actual_1c else None
            is_correct_3c = (actual_3c == direction_pred) if actual_3c else None
            is_correct_5c = (actual_5c == direction_pred) if actual_5c else None
            
            # Actualizar registro solo si tenemos al menos 1 candle verificada
            if actual_1c is not None:
                cursor.execute("""
                    UPDATE predictions
                    SET price_after_1_candle = ?,
                        price_after_3_candles = ?,
                        price_after_5_candles = ?,
                        actual_direction_1c = ?,
                        actual_direction_3c = ?,
                        actual_direction_5c = ?,
                        is_correct_1c = ?,
                        is_correct_3c = ?,
                        is_correct_5c = ?,
                        timestamp_verified = ?
                    WHERE id = ?
                """, (
                    price_1c, price_3c, price_5c,
                    actual_1c, actual_3c, actual_5c,
                    int(is_correct_1c) if is_correct_1c is not None else None,
                    int(is_correct_3c) if is_correct_3c is not None else None,
                    int(is_correct_5c) if is_correct_5c is not None else None,
                    datetime.now().isoformat(),
                    pred_id
                ))
                
                verified_count += 1
        
        conn.commit()
        conn.close()
        
        if verified_count > 0:
            self.logger.info(f"Verificadas {verified_count} predicciones para {symbol}")
        
        return verified_count
    
    def _calculate_direction(self, price_before: float, price_after: float, threshold: float = 0.001) -> str:
        """
        Calcula la dirección del movimiento de precio.
        
        Args:
            price_before: Precio inicial
            price_after: Precio final
            threshold: Umbral mínimo para considerar movimiento (0.1% por defecto)
        
        Returns:
            'UP', 'DOWN', o 'NEUTRAL'
        """
        change_pct = (price_after - price_before) / price_before
        
        if change_pct > threshold:
            return Direction.UP.value
        elif change_pct < -threshold:
            return Direction.DOWN.value
        else:
            return Direction.NEUTRAL.value
    
    def calculate_metrics(self, min_confidence: float = 0.0) -> BacktestResult:
        """
        Calcula métricas de accuracy de las predicciones verificadas.
        
        Args:
            min_confidence: Confianza mínima para filtrar predicciones
        
        Returns:
            BacktestResult con todas las métricas
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Obtener predicciones verificadas
        cursor.execute("""
            SELECT direction_predicted, confidence, quality,
                   is_correct_1c, is_correct_3c, is_correct_5c,
                   actual_direction_1c, actual_direction_3c, actual_direction_5c
            FROM predictions
            WHERE timestamp_verified IS NOT NULL
              AND confidence >= ?
        """, (min_confidence,))
        
        rows = cursor.fetchall()
        conn.close()
        
        if not rows:
            return BacktestResult(
                total_predictions=0,
                accuracy_1c=0.0,
                accuracy_3c=0.0,
                accuracy_5c=0.0,
                accuracy_by_confidence={},
                accuracy_by_quality={},
                confusion_matrix={},
                timestamp=datetime.now().isoformat()
            )
        
        total = len(rows)
        
        # Accuracy general por horizonte
        correct_1c = sum(1 for r in rows if r[3] == 1)
        correct_3c = sum(1 for r in rows if r[4] == 1)
        correct_5c = sum(1 for r in rows if r[5] == 1)
        
        count_1c = sum(1 for r in rows if r[3] is not None)
        count_3c = sum(1 for r in rows if r[4] is not None)
        count_5c = sum(1 for r in rows if r[5] is not None)
        
        acc_1c = correct_1c / count_1c if count_1c > 0 else 0.0
        acc_3c = correct_3c / count_3c if count_3c > 0 else 0.0
        acc_5c = correct_5c / count_5c if count_5c > 0 else 0.0
        
        # Accuracy por rangos de confianza
        acc_by_conf = {}
        confidence_ranges = [
            ("0.50-0.55", 0.50, 0.55),
            ("0.55-0.65", 0.55, 0.65),
            ("0.65-0.75", 0.65, 0.75),
            ("0.75-1.00", 0.75, 1.00)
        ]
        
        for label, min_c, max_c in confidence_ranges:
            filtered = [r for r in rows if min_c <= r[1] < max_c]
            if filtered:
                correct = sum(1 for r in filtered if r[3] == 1)
                acc_by_conf[label] = correct / len(filtered)
        
        # Accuracy por quality
        acc_by_quality = {}
        for quality in ['HIGH', 'MEDIUM', 'LOW']:
            filtered = [r for r in rows if r[2] == quality]
            if filtered:
                correct = sum(1 for r in filtered if r[3] == 1)
                acc_by_quality[quality] = correct / len(filtered)
        
        # Matriz de confusión (1 candle)
        confusion = {}
        for pred_dir in ['UP', 'DOWN', 'NEUTRAL']:
            confusion[pred_dir] = {'UP': 0, 'DOWN': 0, 'NEUTRAL': 0}
        
        for r in rows:
            if r[6]:  # actual_direction_1c
                pred = r[0]
                actual = r[6]
                confusion[pred][actual] += 1
        
        return BacktestResult(
            total_predictions=total,
            accuracy_1c=acc_1c,
            accuracy_3c=acc_3c,
            accuracy_5c=acc_5c,
            accuracy_by_confidence=acc_by_conf,
            accuracy_by_quality=acc_by_quality,
            confusion_matrix=confusion,
            timestamp=datetime.now().isoformat()
        )
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Obtiene un resumen del estado del backtesting.
        
        Returns:
            Diccionario con estadísticas generales
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) FROM predictions")
        total = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE timestamp_verified IS NOT NULL")
        verified = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM predictions WHERE timestamp_verified IS NULL")
        pending = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            "total_predictions": total,
            "verified": verified,
            "pending_verification": pending,
            "last_update": datetime.now().isoformat()
        }
