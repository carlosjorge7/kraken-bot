"""
State Reader Service

Este servicio lee el estado del sistema desde:
- Base de datos SQLite (datos OHLCV y backtesting)
- Archivos JSON (estado actual y alertas)

NO ejecuta lógica de mercado.
NO calcula indicadores.
SOLO lee información generada por el bot.
"""

import json
import sqlite3
from typing import List, Optional, Dict, Any
from datetime import datetime
from pathlib import Path

from backend.app.config import settings
from backend.app.models.schemas import (
    MarketInfo,
    MarketStatus,
    Alert,
    RSIState,
    MarketPrediction,
    Prediction,
    TechnicalScores,
    PredictionDirection,
    PredictionHorizon,
    PredictionQuality,
    BacktestMetrics,
    BacktestSummary
)


class StateReader:
    """
    Servicio para leer el estado del sistema.
    
    Lee información desde archivos y BD sin ejecutar lógica.
    """
    
    def __init__(self):
        self.db_path = settings.DATABASE_PATH
        self.state_file = settings.STATE_FILE
        self.alerts_file = settings.ALERTS_FILE
        
        # Asegurar que existan los archivos
        self._ensure_files()
    
    def _ensure_files(self):
        """Crea archivos de estado si no existen"""
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        Path(self.alerts_file).parent.mkdir(parents=True, exist_ok=True)
        
        if not Path(self.state_file).exists():
            self._write_json(self.state_file, {})
        
        if not Path(self.alerts_file).exists():
            self._write_json(self.alerts_file, {"alerts": []})
    
    def _read_json(self, filepath: str) -> Dict[str, Any]:
        """Lee un archivo JSON"""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, filepath: str, data: Dict[str, Any]):
        """Escribe un archivo JSON"""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    # ========================================================================
    # MARKETS
    # ========================================================================
    
    def get_markets(self) -> List[MarketInfo]:
        """
        Obtiene la lista de mercados monitoreados.
        
        Lee desde el archivo de estado o configuración.
        """
        state = self._read_json(self.state_file)
        markets_data = state.get('markets', [])
        
        # Si no hay en estado, usar valores por defecto
        if not markets_data:
            markets_data = [
                {"symbol": "BTC/USD", "timeframe": "15m"},
                {"symbol": "ETH/USD", "timeframe": "15m"}
            ]
        
        return [MarketInfo(**m) for m in markets_data]
    
    # ========================================================================
    # STATUS
    # ========================================================================
    
    def get_market_status(self, symbol: str) -> Optional[MarketStatus]:
        """
        Obtiene el estado actual de un mercado específico.
        
        Lee desde el archivo de estado generado por el bot.
        """
        state = self._read_json(self.state_file)
        markets_state = state.get('status', {})
        
        if symbol not in markets_state:
            return None
        
        data = markets_state[symbol]
        
        # Procesar predicción si existe
        prediction = None
        if 'prediction' in data and data['prediction']:
            prediction = self._parse_prediction(data['prediction'])
        
        return MarketStatus(
            symbol=symbol,
            timeframe=data.get('timeframe', '15m'),
            last_price=data.get('last_price'),
            rsi_value=data.get('rsi_value'),
            rsi_state=data.get('rsi_state'),
            prediction=prediction,
            last_update=data.get('last_update'),
            data_available=data.get('data_available', False)
        )
    
    def get_all_status(self) -> List[MarketStatus]:
        """
        Obtiene el estado de todos los mercados.
        """
        markets = self.get_markets()
        statuses = []
        
        for market in markets:
            status = self.get_market_status(market.symbol)
            if status:
                statuses.append(status)
            else:
                # Si no hay datos, crear status vacío
                statuses.append(MarketStatus(
                    symbol=market.symbol,
                    timeframe=market.timeframe,
                    data_available=False
                ))
        
        return statuses
    
    # ========================================================================
    # ALERTS
    # ========================================================================
    
    # Mapeo del campo 'type' que escribe el engine al RSIState que espera la API
    _TYPE_TO_RSI_STATE = {
        "rsi_oversold": RSIState.OVERSOLD,
        "rsi_overbought": RSIState.OVERBOUGHT,
    }

    def get_alerts(self, limit: Optional[int] = None) -> List[Alert]:
        """
        Obtiene las alertas guardadas.

        Lee desde el archivo de alertas generado por el bot.
        """
        import logging
        logger = logging.getLogger(__name__)

        alerts_data = self._read_json(self.alerts_file)
        alerts_list = alerts_data.get('alerts', [])

        # Las alertas se insertan al principio (más nuevas primero)
        if limit:
            alerts_list = alerts_list[:limit]

        alerts = []
        for idx, alert_data in enumerate(alerts_list):
            try:
                # El engine escribe 'type' y 'rsi_value'; la API usa 'state' y 'rsi'
                raw_type = alert_data.get('type', '')
                rsi_state = self._TYPE_TO_RSI_STATE.get(raw_type)
                if rsi_state is None:
                    # Intentar parsear directamente por si viene con el formato nuevo
                    rsi_state = RSIState(alert_data['state'])

                rsi_value = alert_data.get('rsi_value') or alert_data.get('rsi')
                if rsi_value is None:
                    raise KeyError('rsi_value/rsi ausente')

                alert = Alert(
                    id=alert_data.get('id', idx),
                    symbol=alert_data['symbol'],
                    rsi=float(rsi_value),
                    state=rsi_state,
                    timestamp=alert_data['timestamp'],
                    message=alert_data.get('message')
                )
                alerts.append(alert)
            except (KeyError, ValueError) as e:
                logger.warning(f"Alerta malformada (idx={idx}): {e} | datos={alert_data}")
                continue

        return alerts
    
    def get_latest_alert(self) -> Optional[Alert]:
        """Obtiene la última alerta registrada"""
        alerts = self.get_alerts(limit=1)
        return alerts[0] if alerts else None
    
    # ========================================================================
    # PREDICTIONS
    # ========================================================================
    
    def _parse_prediction(self, pred_data: Dict[str, Any]) -> Optional[Prediction]:
        """
        Parsea datos de predicción a modelo Pydantic.
        
        Args:
            pred_data: Diccionario con datos de predicción
        
        Returns:
            Prediction object o None si hay error
        """
        try:
            # Parsear scores técnicos si existen
            technical_scores = None
            if 'technical_scores' in pred_data and pred_data['technical_scores']:
                technical_scores = TechnicalScores(**pred_data['technical_scores'])
            
            return Prediction(
                direction=PredictionDirection(pred_data['direction']),
                confidence=pred_data['confidence'],
                horizon=PredictionHorizon(pred_data['horizon']),
                quality=PredictionQuality(pred_data['quality']),
                reasons=pred_data.get('reasons', []),
                technical_scores=technical_scores,
                timestamp=pred_data.get('timestamp', datetime.now().isoformat())
            )
        except (KeyError, ValueError) as e:
            # Si hay error, retornar None
            return None
    
    def get_market_prediction(self, symbol: str) -> Optional[MarketPrediction]:
        """
        Obtiene la predicción para un mercado específico.
        
        Args:
            symbol: Símbolo del mercado
        
        Returns:
            MarketPrediction o None si no hay predicción
        """
        state = self._read_json(self.state_file)
        markets_state = state.get('status', {})
        
        if symbol not in markets_state:
            return None
        
        data = markets_state[symbol]
        
        # Verificar que exista predicción
        if 'prediction' not in data or not data['prediction']:
            return None
        
        prediction = self._parse_prediction(data['prediction'])
        
        if not prediction:
            return None
        
        return MarketPrediction(
            symbol=symbol,
            timeframe=data.get('timeframe', '15m'),
            prediction=prediction
        )
    
    def get_predictions(self) -> List[MarketPrediction]:
        """
        Obtiene predicciones para todos los mercados.
        
        Returns:
            Lista de MarketPrediction
        """
        markets = self.get_markets()
        predictions = []
        
        for market in markets:
            pred = self.get_market_prediction(market.symbol)
            if pred:
                predictions.append(pred)
        
        return predictions
    
    # ========================================================================
    # DATABASE QUERIES (opcional, para datos históricos)
    # ========================================================================
    
    def get_latest_price_from_db(self, symbol: str) -> Optional[float]:
        """
        Obtiene el último precio desde la BD.
        
        Esto es un fallback si el archivo de estado no está disponible.
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT close FROM ohlcv 
                WHERE symbol = ? 
                ORDER BY timestamp DESC 
                LIMIT 1
            """, (symbol,))
            
            result = cursor.fetchone()
            conn.close()
            
            return float(result[0]) if result else None
            
        except Exception:
            return None
    
    # ========================================================================
    # UTILITY
    # ========================================================================
    
    def update_state(self, symbol: str, data: Dict[str, Any]):
        """
        Actualiza el estado de un símbolo.
        
        NOTA: Este método es llamado por el BOT, no por la API.
        """
        state = self._read_json(self.state_file)
        
        if 'status' not in state:
            state['status'] = {}
        
        state['status'][symbol] = data
        
        self._write_json(self.state_file, state)
    
    def add_alert(self, alert: Dict[str, Any]):
        """
        Añade una nueva alerta.
        
        NOTA: Este método es llamado por el BOT, no por la API.
        """
        alerts_data = self._read_json(self.alerts_file)
        
        if 'alerts' not in alerts_data:
            alerts_data['alerts'] = []
        
        # Añadir timestamp si no existe
        if 'timestamp' not in alert:
            alert['timestamp'] = datetime.now().isoformat()
        
        alerts_data['alerts'].append(alert)
        
        # Mantener solo las últimas N alertas
        max_alerts = settings.MAX_ALERTS_HISTORY
        if len(alerts_data['alerts']) > max_alerts:
            alerts_data['alerts'] = alerts_data['alerts'][-max_alerts:]
        
        self._write_json(self.alerts_file, alerts_data)
    
    # ========================================================================
    # BACKTESTING METHODS
    # ========================================================================
    
    def get_backtest_metrics(
        self,
        symbol: Optional[str] = None,
        min_confidence: Optional[float] = None
    ) -> Optional[BacktestMetrics]:
        """
        Lee métricas de backtesting desde la BD.
        
        Args:
            symbol: Filtrar por símbolo
            min_confidence: Confianza mínima
        
        Returns:
            Métricas agregadas o None
        """
        try:
            backtest_db = Path("data/backtesting.db")
            if not backtest_db.exists():
                return None
            
            conn = sqlite3.connect(backtest_db)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Query base - usar actual_direction_1c como referencia principal
            where_clauses = ["actual_direction_1c IS NOT NULL"]
            params = []
            
            if symbol:
                where_clauses.append("symbol = ?")
                params.append(symbol)
            
            if min_confidence is not None:
                where_clauses.append("confidence >= ?")
                params.append(min_confidence)
            
            where_sql = " AND ".join(where_clauses)
            
            # Total predictions
            cursor.execute(f"""
                SELECT COUNT(*) as total
                FROM predictions
                WHERE {where_sql}
            """, params)
            total = cursor.fetchone()['total']
            
            if total == 0:
                conn.close()
                return None
            
            # Accuracy por horizonte
            accuracy_1c = self._calculate_accuracy(cursor, where_sql, params, 1)
            accuracy_3c = self._calculate_accuracy(cursor, where_sql, params, 3)
            accuracy_5c = self._calculate_accuracy(cursor, where_sql, params, 5)
            
            # Accuracy por confidence
            acc_by_conf = self._calculate_accuracy_by_confidence(
                cursor, where_sql, params
            )
            
            # Accuracy por quality
            acc_by_quality = self._calculate_accuracy_by_quality(
                cursor, where_sql, params
            )
            
            # Confusion matrix
            confusion = self._calculate_confusion_matrix(cursor, where_sql, params)
            
            conn.close()
            
            return BacktestMetrics(
                total_predictions=total,
                accuracy_1c=accuracy_1c,
                accuracy_3c=accuracy_3c,
                accuracy_5c=accuracy_5c,
                accuracy_by_confidence=acc_by_conf,
                accuracy_by_quality=acc_by_quality,
                confusion_matrix=confusion,
                timestamp=datetime.now().isoformat()
            )
        
        except Exception as e:
            print(f"⚠️  Error obteniendo métricas de backtesting: {e}")
            return None
    
    def get_backtest_summary(self) -> Optional[BacktestSummary]:
        """
        Lee resumen de backtesting.
        
        Returns:
            Resumen básico o None
        """
        try:
            backtest_db = Path("data/backtesting.db")
            if not backtest_db.exists():
                return None
            
            conn = sqlite3.connect(backtest_db)
            cursor = conn.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM predictions")
            total = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT COUNT(*) FROM predictions
                WHERE actual_direction_1c IS NOT NULL
            """)
            verified = cursor.fetchone()[0]
            
            cursor.execute("""
                SELECT MAX(timestamp_predicted) FROM predictions
            """)
            last_update = cursor.fetchone()[0] or datetime.now().isoformat()
            
            conn.close()
            
            return BacktestSummary(
                total_predictions=total,
                verified=verified,
                pending_verification=total - verified,
                last_update=last_update
            )
        
        except Exception as e:
            print(f"⚠️  Error obteniendo resumen de backtesting: {e}")
            return None
    
    def _calculate_accuracy(
        self,
        cursor,
        where_sql: str,
        params: list,
        candles: int
    ) -> float:
        """Calcula accuracy para un horizonte específico"""
        # Determinar la columna de dirección basada en el horizonte
        direction_col = f"actual_direction_{candles}c"
        cursor.execute(f"""
            SELECT
                SUM(CASE WHEN direction_predicted = {direction_col} THEN 1 ELSE 0 END) as correct,
                COUNT(*) as total
            FROM predictions
            WHERE {where_sql} AND {direction_col} IS NOT NULL
        """)
        
        row = cursor.fetchone()
        if row[1] == 0:
            return 0.0
        
        return round(row[0] / row[1], 4)
    
    def _calculate_accuracy_by_confidence(
        self,
        cursor,
        where_sql: str,
        params: list
    ) -> Dict[str, float]:
        """Calcula accuracy por rangos de confianza"""
        bins = [
            ("0.50-0.55", 0.50, 0.55),
            ("0.55-0.65", 0.55, 0.65),
            ("0.65-0.75", 0.65, 0.75),
            ("0.75-1.00", 0.75, 1.00)
        ]
        
        result = {}
        for label, min_conf, max_conf in bins:
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN direction_predicted = actual_direction_1c THEN 1 ELSE 0 END) as correct,
                    COUNT(*) as total
                FROM predictions
                WHERE {where_sql}
                  AND confidence >= ?
                  AND confidence < ?
            """, params + [min_conf, max_conf])
            
            row = cursor.fetchone()
            if row[1] > 0:
                result[label] = round(row[0] / row[1], 4)
        
        return result
    
    def _calculate_accuracy_by_quality(
        self,
        cursor,
        where_sql: str,
        params: list
    ) -> Dict[str, float]:
        """Calcula accuracy por calidad"""
        qualities = ["LOW", "MEDIUM", "HIGH"]
        result = {}
        
        for quality in qualities:
            cursor.execute(f"""
                SELECT
                    SUM(CASE WHEN direction_predicted = actual_direction_1c THEN 1 ELSE 0 END) as correct,
                    COUNT(*) as total
                FROM predictions
                WHERE {where_sql} AND quality = ?
            """, params + [quality])
            
            row = cursor.fetchone()
            if row[1] > 0:
                result[quality] = round(row[0] / row[1], 4)
        
        return result
    
    def _calculate_confusion_matrix(
        self,
        cursor,
        where_sql: str,
        params: list
    ) -> Dict[str, Dict[str, int]]:
        """Calcula matriz de confusión"""
        directions = ["UP", "DOWN", "NEUTRAL"]
        matrix = {}
        
        for predicted in directions:
            matrix[predicted] = {}
            for actual in directions:
                cursor.execute(f"""
                    SELECT COUNT(*)
                    FROM predictions
                    WHERE {where_sql}
                      AND direction_predicted = ?
                      AND actual_direction_1c = ?
                """, params + [predicted, actual])
                
                matrix[predicted][actual] = cursor.fetchone()[0]
        
        return matrix


# Singleton instance
state_reader = StateReader()
