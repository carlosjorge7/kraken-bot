"""
Kraken Client - Cliente para interactuar con la API pública de Kraken

Esta clase es responsable ÚNICAMENTE de obtener datos del exchange.
NO contiene lógica de negocio, indicadores ni estrategias.
"""

import logging
from datetime import datetime
from typing import Optional
import ccxt
import pandas as pd


class KrakenClient:
    """
    Cliente para interactuar con la API pública de Kraken.
    
    Este cliente utiliza la librería ccxt para acceder a datos OHLCV
    (Open, High, Low, Close, Volume) del exchange Kraken.
    """
    
    def __init__(self):
        """
        Inicializa el cliente de Kraken.
        
        IMPORTANTE: Solo usa la API pública, no requiere credenciales.
        """
        self.logger = logging.getLogger(__name__)
        self.logger.info("Inicializando KrakenClient...")
        
        try:
            # Inicializar exchange sin credenciales (solo API pública)
            self.exchange = ccxt.kraken({
                'enableRateLimit': True,  # Respetar límites de rate
                'timeout': 30000,  # Timeout de 30 segundos
            })
            self.logger.info("KrakenClient inicializado correctamente")
            
        except Exception as e:
            self.logger.error(f"Error al inicializar KrakenClient: {e}")
            raise
    
    def fetch_ohlcv(
        self,
        symbol: str,
        timeframe: str = '15m',
        limit: int = 100,
        since: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Obtiene datos OHLCV (velas) de Kraken.
        
        Args:
            symbol: Par de trading (ej: 'BTC/USD')
            timeframe: Marco temporal (ej: '1m', '5m', '15m', '1h', '1d')
            limit: Número de velas a obtener (máximo depende del exchange)
            since: Timestamp en milisegundos desde el cual obtener datos (opcional)
        
        Returns:
            pd.DataFrame: DataFrame con columnas:
                - timestamp: Fecha/hora de la vela (datetime)
                - open: Precio de apertura
                - high: Precio máximo
                - low: Precio mínimo
                - close: Precio de cierre
                - volume: Volumen negociado
        
        Raises:
            Exception: Si hay error en la conexión o petición
        """
        try:
            self.logger.info(
                f"Descargando datos OHLCV: {symbol}, "
                f"timeframe={timeframe}, limit={limit}"
            )
            
            # Obtener datos del exchange
            ohlcv = self.exchange.fetch_ohlcv(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit,
                since=since
            )
            
            if not ohlcv:
                self.logger.warning("No se obtuvieron datos del exchange")
                return pd.DataFrame()
            
            # Convertir a DataFrame
            df = pd.DataFrame(
                ohlcv,
                columns=['timestamp', 'open', 'high', 'low', 'close', 'volume']
            )
            
            # Convertir timestamp de milisegundos a datetime
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            
            # Agregar información del símbolo
            df['symbol'] = symbol
            
            self.logger.info(
                f"Datos obtenidos exitosamente. "
                f"Total de velas: {len(df)}, "
                f"Rango: {df['timestamp'].min()} a {df['timestamp'].max()}"
            )
            
            return df
            
        except ccxt.NetworkError as e:
            self.logger.error(f"Error de red al conectar con Kraken: {e}")
            raise
        except ccxt.ExchangeError as e:
            self.logger.error(f"Error del exchange Kraken: {e}")
            raise
        except Exception as e:
            self.logger.error(f"Error inesperado al obtener datos OHLCV: {e}")
            raise
    
    def get_exchange_info(self) -> dict:
        """
        Obtiene información básica del exchange.
        
        Returns:
            dict: Información del exchange (nombre, versión, etc.)
        """
        try:
            info = {
                'name': self.exchange.name,
                'id': self.exchange.id,
                'version': getattr(self.exchange, 'version', 'N/A'),
                'has': {
                    'fetchOHLCV': self.exchange.has.get('fetchOHLCV', False),
                    'fetchTicker': self.exchange.has.get('fetchTicker', False),
                }
            }
            return info
        except Exception as e:
            self.logger.error(f"Error al obtener información del exchange: {e}")
            return {}
    
    def check_connection(self) -> bool:
        """
        Verifica que la conexión con Kraken esté funcionando.
        
        Returns:
            bool: True si la conexión es exitosa, False en caso contrario
        """
        try:
            self.logger.debug("Verificando conexión con Kraken...")
            # Intentar obtener una vela para verificar conexión
            test_data = self.exchange.fetch_ohlcv('BTC/USD', '1h', limit=1)
            self.logger.info("✓ Conexión con Kraken verificada")
            return len(test_data) > 0
        except Exception as e:
            self.logger.error(f"✗ Error al verificar conexión: {e}")
            return False
