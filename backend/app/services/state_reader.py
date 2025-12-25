"""
State Reader Service

Este servicio lee el estado del sistema desde:
- Base de datos SQLite (datos OHLCV)
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
    RSIState
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
        
        return MarketStatus(
            symbol=symbol,
            timeframe=data.get('timeframe', '15m'),
            last_price=data.get('last_price'),
            rsi_value=data.get('rsi_value'),
            rsi_state=data.get('rsi_state'),
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
    
    def get_alerts(self, limit: Optional[int] = None) -> List[Alert]:
        """
        Obtiene las alertas guardadas.
        
        Lee desde el archivo de alertas generado por el bot.
        """
        alerts_data = self._read_json(self.alerts_file)
        alerts_list = alerts_data.get('alerts', [])
        
        # Aplicar límite si se especifica
        if limit:
            alerts_list = alerts_list[-limit:]
        
        # Convertir a modelos Pydantic
        alerts = []
        for idx, alert_data in enumerate(alerts_list):
            try:
                alert = Alert(
                    id=idx,
                    symbol=alert_data['symbol'],
                    rsi=alert_data['rsi'],
                    state=RSIState(alert_data['state']),
                    timestamp=alert_data['timestamp'],
                    message=alert_data.get('message')
                )
                alerts.append(alert)
            except (KeyError, ValueError):
                # Ignorar alertas malformadas
                continue
        
        return alerts
    
    def get_latest_alert(self) -> Optional[Alert]:
        """Obtiene la última alerta registrada"""
        alerts = self.get_alerts(limit=1)
        return alerts[0] if alerts else None
    
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


# Singleton instance
state_reader = StateReader()
