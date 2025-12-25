"""
Engine - Motor Principal del Bot

Esta clase orquesta todo el sistema: obtiene datos del mercado,
procesa información y coordina los diferentes módulos.

NO contiene lógica de trading, solo lectura y procesamiento de datos.
"""

import logging
import time
import signal
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
import pandas as pd
from fetcher.kraken_client import KrakenClient
from data.database import DatabaseManager
from indicators.rsi import calculate_rsi, get_rsi_signal


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
        
        # Estado previo de RSI para detección de cruces
        # Clave: símbolo, Valor: último estado ('NEUTRAL', 'OVERBOUGHT', 'OVERSOLD')
        self.rsi_states: Dict[str, str] = {}
        
        # Archivos de estado para compartir con la API
        self.state_file = "data/bot_state.json"
        self.alerts_file = "data/alerts.json"
        self._ensure_state_files()
        
        self.logger.info("Engine inicializado correctamente")
    
    def _ensure_state_files(self):
        """Asegura que existan los archivos de estado."""
        Path(self.state_file).parent.mkdir(parents=True, exist_ok=True)
        
        if not Path(self.state_file).exists():
            self._write_json(self.state_file, {})
        
        if not Path(self.alerts_file).exists():
            self._write_json(self.alerts_file, {"alerts": []})
    
    def _read_json(self, filepath: str) -> Dict[str, Any]:
        """Lee un archivo JSON."""
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return {}
    
    def _write_json(self, filepath: str, data: Dict[str, Any]):
        """Escribe un archivo JSON."""
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _save_state(self, markets_data: List[Dict[str, Any]]):
        """Guarda el estado actual del bot para que la API lo lea."""
        state = {
            "markets": [{"symbol": s, "timeframe": self.timeframe} for s in self.symbols],
            "status": {},
            "last_update": datetime.now().isoformat()
        }
        
        # Agregar estado de cada mercado
        for market_data in markets_data:
            symbol = market_data['symbol']
            state['status'][symbol] = {
                "timeframe": self.timeframe,
                "last_price": market_data.get('last_price'),
                "rsi_value": market_data.get('rsi_value'),
                "rsi_state": market_data.get('rsi_state'),
                "last_update": datetime.now().isoformat(),
                "data_available": True
            }
        
        self._write_json(self.state_file, state)
        self.logger.debug(f"Estado guardado en {self.state_file}")
    
    def _add_alert(self, symbol: str, alert_type: str, message: str, rsi_value: float = None):
        """Agrega una alerta al archivo de alertas."""
        alerts_data = self._read_json(self.alerts_file)
        
        if 'alerts' not in alerts_data:
            alerts_data['alerts'] = []
        
        alert = {
            "id": len(alerts_data['alerts']) + 1,
            "symbol": symbol,
            "type": alert_type,
            "message": message,
            "rsi_value": rsi_value,
            "timestamp": datetime.now().isoformat(),
            "acknowledged": False
        }
        
        alerts_data['alerts'].insert(0, alert)  # Nuevas primero
        
        # Mantener solo las últimas 100 alertas
        alerts_data['alerts'] = alerts_data['alerts'][:100]
        
        self._write_json(self.alerts_file, alerts_data)
        self.logger.debug(f"Alerta guardada: {message}")
    
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
        markets_state = []
        
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
                
                # Procesar y mostrar información (ahora retorna datos de estado)
                market_data = self._display_market_summary(df, symbol)
                if market_data:
                    markets_state.append(market_data)
                
                # Guardar en base de datos
                inserted = self.db.save_ohlcv(df)
                total_records = self.db.count_records(symbol)
                self.logger.info(f"BD: {inserted} nuevas | Total {symbol}: {total_records}")
                
                all_data.append(df)
            
            # 3. Guardar estado para la API
            if markets_state:
                self._save_state(markets_state)
            
            self.logger.info("\n" + "=" * 60)
            self.logger.info("CICLO COMPLETADO EXITOSAMENTE")
            self.logger.info(f"Procesados {len(all_data)} símbolos")
            self.logger.info("=" * 60)
            
            # Retornar el último DataFrame (por compatibilidad)
            return all_data[-1] if all_data else pd.DataFrame()
            
        except Exception as e:
            self.logger.error(f"Error durante la ejecución del ciclo: {e}")
            raise
    
    def _display_market_summary(self, df: pd.DataFrame, symbol: str = None) -> Optional[Dict[str, Any]]:
        """
        Muestra un resumen de los datos del mercado y retorna datos para guardar estado.
        
        Args:
            df: DataFrame con datos OHLCV
            symbol: Símbolo del par (opcional)
            
        Returns:
            Dict con datos del mercado para guardar en estado
        """
        if df.empty:
            return None
        
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
        self.logger.info("")
        
        # Calcular y mostrar RSI
        rsi_value = None
        rsi_signal = None
        
        try:
            rsi_period = 14
            rsi_series = calculate_rsi(df, period=rsi_period)
            
            # Usar última vela cerrada (no la actual)
            if len(rsi_series) >= 2 and pd.notna(rsi_series.iloc[-2]):
                rsi_value = float(rsi_series.iloc[-2])
                rsi_signal = get_rsi_signal(rsi_value)
                self.logger.info(f"📉 RSI ({rsi_period}): {rsi_value:.2f} → {rsi_signal}")
                
                # Procesar alertas condicionales
                self._process_rsi_alert(display_symbol, rsi_value, rsi_signal)
                
            elif len(rsi_series) >= 1 and pd.notna(rsi_series.iloc[-1]):
                rsi_value = float(rsi_series.iloc[-1])
                rsi_signal = get_rsi_signal(rsi_value)
                self.logger.info(f"📉 RSI ({rsi_period}): {rsi_value:.2f} → {rsi_signal}")
                
                # Procesar alertas condicionales
                self._process_rsi_alert(display_symbol, rsi_value, rsi_signal)
                
            else:
                self.logger.info(f"📉 RSI ({rsi_period}): No disponible (datos insuficientes)")
        except Exception as e:
            self.logger.info(f"📉 RSI: No disponible (error: {e})")
        
        self.logger.info("-" * 60)
        self.logger.info("")
        
        # Retornar datos para guardar en estado
        return {
            "symbol": display_symbol,
            "last_price": float(latest['close']),
            "rsi_value": rsi_value,
            "rsi_state": rsi_signal
        }
    
    def _process_rsi_alert(self, symbol: str, rsi_value: float, rsi_signal: str) -> None:
        """
        Procesa alertas condicionales basadas en RSI.
        
        Solo emite alertas cuando el RSI CRUZA hacia una zona extrema,
        evitando alertas repetidas en cada ciclo.
        
        Args:
            symbol: Símbolo del par (ej: BTC/USD)
            rsi_value: Valor actual del RSI
            rsi_signal: Señal del RSI ('NEUTRAL', 'OVERBOUGHT', 'OVERSOLD')
        """
        # Obtener estado previo (por defecto NEUTRAL si es la primera vez)
        previous_state = self.rsi_states.get(symbol, 'NEUTRAL')
        current_state = rsi_signal
        
        # Solo alertar si hay un CRUCE desde NEUTRAL hacia zona extrema
        alert_triggered = False
        
        if previous_state == 'NEUTRAL' and current_state == 'OVERSOLD':
            # Cruce a sobreventa
            message = f"RSI en sobreventa: {symbol} | RSI {rsi_value:.1f} | {self.timeframe}"
            self.logger.info(f"⚠️ {message}")
            self._add_alert(symbol, "rsi_oversold", message, rsi_value)
            alert_triggered = True
        
        elif previous_state == 'NEUTRAL' and current_state == 'OVERBOUGHT':
            # Cruce a sobrecompra
            message = f"RSI en sobrecompra: {symbol} | RSI {rsi_value:.1f} | {self.timeframe}"
            self.logger.info(f"⚠️ {message}")
            self._add_alert(symbol, "rsi_overbought", message, rsi_value)
            alert_triggered = True
        
        # Actualizar estado actual
        self.rsi_states[symbol] = current_state

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
    
    def run_continuous(self, setup_signals=True):
        """
        Ejecuta el bot en loop continuo.
        
        Este método corre indefinidamente hasta recibir señal de shutdown.
        
        Args:
            setup_signals: Si es True, configura signal handlers (solo funciona en thread principal)
        """
        self.running = True
        self.logger.info("Modo continuo activado")
        self.logger.info(f"Intervalo: {self.interval}s")
        
        # Configurar señales para graceful shutdown (solo si es thread principal)
        if setup_signals:
            try:
                signal.signal(signal.SIGTERM, self._signal_handler)
                signal.signal(signal.SIGINT, self._signal_handler)
            except ValueError:
                # No estamos en el thread principal, ignorar
                self.logger.debug("Signal handlers no configurados (no estamos en thread principal)")
        
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
