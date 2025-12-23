"""
Engine - Motor Principal del Bot

Esta clase orquesta todo el sistema: obtiene datos del mercado,
procesa información y coordina los diferentes módulos.

NO contiene lógica de trading, solo lectura y procesamiento de datos.
"""

import logging
import time
import signal
from typing import Dict, Any, Optional
import pandas as pd
from fetcher.kraken_client import KrakenClient
from data.database import DatabaseManager


class Engine:
    """
    Motor principal del sistema de lectura de mercado.
    
    Este motor es el orquestador central que coordina:
    - Obtención de datos del mercado (via KrakenClient)
    - Procesamiento de información
    - (Futuro) Cálculo de indicadores
    - (Futuro) Generación de alertas
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el motor del bot.
        
        Args:
            config: Diccionario con toda la configuración del sistema
        """
        self.logger = logging.getLogger(__name__)
        self.config = config
        self.logger.info("Inicializando Engine...")
        
        # Control de ejecución
        self.running = False
        self.shutdown_requested = False
        
        # Configuración del exchange
        self.symbols = config['exchange']['symbols']
        self.timeframe = config['exchange']['timeframe']
        self.limit = config['exchange']['limit']
        
        # Configuración de loop
        self.interval = config.get('scheduler', {}).get('interval', 300)
        self.max_retries = config.get('scheduler', {}).get('max_retries', 3)
        self.retry_delay = config.get('scheduler', {}).get('retry_delay', 60)
        
        # Inicializar cliente de Kraken
        try:
            self.kraken_client = KrakenClient()
            self.logger.info("KrakenClient inicializado")
        except Exception as e:
            self.logger.error(f"Error al inicializar KrakenClient: {e}")
            raise
        
        # Inicializar base de datos
        try:
            db_path = config['database']['path']
            self.db = DatabaseManager(db_path)
            self.logger.info("Base de datos inicializada")
        except Exception as e:
            self.logger.error(f"Error al inicializar BD: {e}")
            raise
        
        self.logger.info("Engine inicializado correctamente")
    
    def run(self) -> pd.DataFrame:
        """
        Ejecuta el ciclo principal del bot.
        
        Este método:
        1. Verifica la conexión con Kraken
        2. Obtiene datos OHLCV del mercado para cada símbolo
        3. Procesa y muestra información básica
        4. (Futuro) Calculará indicadores y generará alertas
        
        Returns:
            pd.DataFrame: Datos OHLCV obtenidos (último símbolo procesado)
        """
        self.logger.info("=" * 60)
        self.logger.info("INICIANDO CICLO DE LECTURA DE MERCADO")
        self.logger.info("=" * 60)
        
        all_data = []
        
        try:
            # 1. Verificar conexión
            self.logger.info("Paso 1: Verificando conexión con Kraken...")
            if not self.kraken_client.check_connection():
                raise ConnectionError("No se pudo conectar con Kraken")
            
            # 2. Procesar cada símbolo
            for idx, symbol in enumerate(self.symbols, 1):
                self.logger.info(f"\nProcesando símbolo {idx}/{len(self.symbols)}: {symbol}")
                
                # Obtener datos del mercado
                df = self.kraken_client.fetch_ohlcv(
                    symbol=symbol,
                    timeframe=self.timeframe,
                    limit=self.limit
                )
                
                if df.empty:
                    self.logger.warning(f"No se obtuvieron datos para {symbol}")
                    continue
                
                # Procesar y mostrar información
                self._display_market_summary(df, symbol)
                
                # Guardar en base de datos
                inserted = self.db.save_ohlcv(df)
                total_records = self.db.count_records(symbol)
                self.logger.info(f"BD: {inserted} nuevas | Total {symbol}: {total_records}")
                
                all_data.append(df)
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("CICLO COMPLETADO EXITOSAMENTE")
            self.logger.info(f"Procesados {len(all_data)} símbolos")
            self.logger.info("=" * 60)
            
            # Retornar el último DataFrame (por compatibilidad)
            return all_data[-1] if all_data else pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error durante la ejecución del ciclo: {e}")
            raise
    
    def _display_market_summary(self, df: pd.DataFrame, symbol: str = None) -> None:
        """
        Muestra un resumen de los datos del mercado.
        
        Args:
            df: DataFrame con datos OHLCV
            symbol: Símbolo del par (opcional)
        """
        if df.empty:
            return
        
        # Obtener la última vela (dato más reciente)
        latest = df.iloc[-1]
        
        # Calcular estadísticas básicas
        price_min = df['low'].min()
        price_max = df['high'].max()
        avg_volume = df['volume'].mean()
        
        # Calcular cambio de precio en el periodo
        price_change = latest['close'] - df.iloc[0]['open']
        price_change_pct = (price_change / df.iloc[0]['open']) * 100
        
        display_symbol = symbol or latest.get('symbol', 'N/A')
        
        self.logger.info("")
        self.logger.info(f"📊 RESUMEN: {display_symbol}")
        self.logger.info("-" * 60)
        self.logger.info(f"Timeframe:        {self.timeframe}")
        self.logger.info(f"Total de velas:   {len(df)}")
        self.logger.info(f"Periodo:          {df['timestamp'].min()} → {df['timestamp'].max()}")
        self.logger.info("")
        self.logger.info(f"💰 ÚLTIMA VELA ({latest['timestamp']})")
        self.logger.info(f"  Apertura:       ${latest['open']:,.2f}")
        self.logger.info(f"  Máximo:         ${latest['high']:,.2f}")
        self.logger.info(f"  Mínimo:         ${latest['low']:,.2f}")
        self.logger.info(f"  Cierre:         ${latest['close']:,.2f}")
        self.logger.info(f"  Volumen:        {latest['volume']:,.4f}")
        self.logger.info("")
        self.logger.info(f"📈 ESTADÍSTICAS DEL PERIODO")
        self.logger.info(f"  Precio mínimo:  ${price_min:,.2f}")
        self.logger.info(f"  Precio máximo:  ${price_max:,.2f}")
        self.logger.info(f"  Cambio:         ${price_change:+,.2f} ({price_change_pct:+.2f}%)")
        self.logger.info(f"  Vol. promedio:  {avg_volume:,.4f}")
        self.logger.info("-" * 60)
        self.logger.info("")
    
    def get_latest_price(self, symbol: str = None) -> float:
        """
        Obtiene el precio más reciente del mercado.
        
        Args:
            symbol: Símbolo a consultar (usa el primero de la lista si no se especifica)
        
        Returns:
            float: Precio de cierre de la última vela
        """
        try:
            target_symbol = symbol or self.symbols[0]
            df = self.kraken_client.fetch_ohlcv(
                symbol=target_symbol,
                timeframe=self.timeframe,
                limit=1
            )
            if not df.empty:
                return float(df.iloc[-1]['close'])
            return 0.0
        except Exception as e:
            self.logger.error(f"Error al obtener último precio: {e}")
            return 0.0
    
    def run_once_with_retry(self) -> Optional[pd.DataFrame]:
        """
        Ejecuta un ciclo con reintentos automáticos.
        
        Returns:
            DataFrame con datos o None si falla
        """
        for attempt in range(1, self.max_retries + 1):
            try:
                return self.run()
            except Exception as e:
                self.logger.error(f"Error en intento {attempt}/{self.max_retries}: {e}")
                
                if attempt < self.max_retries:
                    self.logger.info(f"Reintentando en {self.retry_delay}s...")
                    time.sleep(self.retry_delay)
                else:
                    self.logger.error("Máximo de reintentos alcanzado")
        
        return None
    
    def run_continuous(self):
        """
        Ejecuta el bot en loop continuo.
        
        Este método corre indefinidamente hasta recibir señal de shutdown.
        """
        self.running = True
        self.logger.info("Modo continuo activado")
        self.logger.info(f"Intervalo: {self.interval}s")
        
        # Configurar señales para graceful shutdown
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        cycle_count = 0
        
        while self.running and not self.shutdown_requested:
            cycle_count += 1
            self.logger.info(f"\n{'='*60}")
            self.logger.info(f"CICLO #{cycle_count}")
            self.logger.info(f"{'='*60}")
            
            # Ejecutar ciclo con reintentos
            result = self.run_once_with_retry()
            
            if result is None:
                self.logger.warning("Ciclo falló después de todos los reintentos")
            
            # Esperar hasta el próximo ciclo
            if self.running and not self.shutdown_requested:
                self.logger.info(f"Esperando {self.interval}s hasta el próximo ciclo...")
                
                # Sleep con verificación de shutdown cada segundo
                for _ in range(self.interval):
                    if self.shutdown_requested:
                        break
                    time.sleep(1)
        
        self.logger.info("Bot detenido correctamente")
    
    def _signal_handler(self, signum, frame):
        """
        Maneja señales de sistema para graceful shutdown.
        """
        signal_name = 'SIGTERM' if signum == signal.SIGTERM else 'SIGINT'
        self.logger.warning(f"Señal {signal_name} recibida - iniciando shutdown...")
        self.shutdown_requested = True
        self.running = False
    
    def stop(self):
        """
        Detiene el bot de forma limpia.
        """
        self.logger.info("Deteniendo bot...")
        self.running = False
        self.shutdown_requested = True
