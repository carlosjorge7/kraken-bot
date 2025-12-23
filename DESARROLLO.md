# 🛠️ Guía de Desarrollo - Kraken Bot

Esta guía está dirigida a desarrolladores que quieran extender o personalizar el bot.

## 📁 Arquitectura del Proyecto

### Separación de Responsabilidades

El proyecto sigue el principio de **Separación de Responsabilidades (SoC)**:

```
┌─────────────────────────────────────────────────────────────┐
│                        main.py                              │
│                   (Punto de Entrada)                        │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                      core/engine.py                         │
│                   (Orquestador Central)                     │
└───┬─────────────────┬─────────────────┬────────────────┬────┘
    │                 │                 │                │
    ▼                 ▼                 ▼                ▼
┌─────────┐    ┌──────────┐    ┌───────────┐    ┌──────────┐
│fetcher/ │    │indicators│    │  alerts/  │    │  data/   │
│         │    │    /     │    │           │    │          │
└─────────┘    └──────────┘    └───────────┘    └──────────┘
```

### Módulos y sus Funciones

#### 1. **fetcher/** - Obtención de Datos

- **Responsabilidad**: SOLO obtener datos de exchanges
- **NO debe contener**: Lógica de negocio, indicadores, estrategias
- **Puede añadirse**: Clientes para otros exchanges (Binance, Coinbase, etc.)

#### 2. **core/** - Motor Central

- **Responsabilidad**: Orquestación y coordinación
- **Contiene**: Flujos de trabajo, procesamiento de datos
- **NO debe contener**: Implementación de indicadores o conexiones directas a APIs

#### 3. **indicators/** - Indicadores Técnicos

- **Responsabilidad**: Cálculos matemáticos puros
- **Entrada**: DataFrames de pandas
- **Salida**: DataFrames con nuevas columnas o valores calculados
- **NO debe contener**: Lógica de trading o decisiones

#### 4. **alerts/** - Sistema de Notificaciones

- **Responsabilidad**: Envío de alertas a diferentes canales
- **Estado actual**: Stub (preparado para implementación)
- **Futuro**: Email, Discord, Slack, etc.

---

## 🔧 Cómo Extender el Bot

### 1. Añadir un Nuevo Indicador

Crear un archivo en `indicators/`:

```python
# indicators/macd.py
"""
MACD - Moving Average Convergence Divergence
"""

import pandas as pd

def calculate_macd(
    df: pd.DataFrame,
    fast_period: int = 12,
    slow_period: int = 26,
    signal_period: int = 9
) -> pd.DataFrame:
    """
    Calcula el MACD.

    Args:
        df: DataFrame con datos OHLCV
        fast_period: Periodo de EMA rápida
        slow_period: Periodo de EMA lenta
        signal_period: Periodo de señal

    Returns:
        DataFrame con columnas 'macd', 'signal', 'histogram'
    """
    result_df = df.copy()

    # Calcular EMAs
    ema_fast = df['close'].ewm(span=fast_period).mean()
    ema_slow = df['close'].ewm(span=slow_period).mean()

    # MACD Line
    result_df['macd'] = ema_fast - ema_slow

    # Signal Line
    result_df['signal'] = result_df['macd'].ewm(span=signal_period).mean()

    # Histogram
    result_df['histogram'] = result_df['macd'] - result_df['signal']

    return result_df
```

Actualizar `indicators/__init__.py`:

```python
from .rsi import calculate_rsi
from .macd import calculate_macd

__all__ = ['calculate_rsi', 'calculate_macd']
```

### 2. Integrar Indicador en el Engine

Modificar `core/engine.py`:

```python
from indicators import calculate_rsi, calculate_macd

def run(self) -> pd.DataFrame:
    # ... código existente ...

    # 4. Calcular indicadores
    self.logger.info("Paso 4: Calculando indicadores técnicos...")
    df = calculate_rsi(df, period=14)
    df = calculate_macd(df)

    # Mostrar últimos valores
    latest = df.iloc[-1]
    self.logger.info(f"RSI: {latest['rsi']:.2f}")
    self.logger.info(f"MACD: {latest['macd']:.4f}")

    return df
```

### 3. Implementar Base de Datos

Crear `data/database.py`:

```python
"""
Database Manager - Gestión de Base de Datos SQLite
"""

import sqlite3
import pandas as pd
from typing import Optional
import logging

class DatabaseManager:
    """
    Gestor de base de datos para almacenar datos OHLCV.
    """

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        self._create_tables()

    def _create_tables(self):
        """Crea las tablas necesarias si no existen."""
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
                UNIQUE(timestamp, symbol)
            )
        """)

        conn.commit()
        conn.close()
        self.logger.info(f"Base de datos inicializada: {self.db_path}")

    def save_ohlcv(self, df: pd.DataFrame) -> int:
        """
        Guarda datos OHLCV en la base de datos.

        Args:
            df: DataFrame con datos OHLCV

        Returns:
            Número de filas insertadas
        """
        conn = sqlite3.connect(self.db_path)

        # Insertar o ignorar duplicados
        rows_before = self._count_rows(conn)
        df.to_sql('ohlcv', conn, if_exists='append', index=False)
        rows_after = self._count_rows(conn)

        conn.close()

        inserted = rows_after - rows_before
        self.logger.info(f"Guardadas {inserted} nuevas velas en la BD")
        return inserted

    def get_ohlcv(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: Optional[int] = None
    ) -> pd.DataFrame:
        """
        Obtiene datos OHLCV de la base de datos.

        Args:
            symbol: Par de trading
            start_date: Fecha de inicio (opcional)
            end_date: Fecha de fin (opcional)
            limit: Límite de registros (opcional)

        Returns:
            DataFrame con datos OHLCV
        """
        conn = sqlite3.connect(self.db_path)

        query = "SELECT * FROM ohlcv WHERE symbol = ?"
        params = [symbol]

        if start_date:
            query += " AND timestamp >= ?"
            params.append(start_date)

        if end_date:
            query += " AND timestamp <= ?"
            params.append(end_date)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += f" LIMIT {limit}"

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        return df

    def _count_rows(self, conn) -> int:
        """Cuenta el número total de filas."""
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM ohlcv")
        return cursor.fetchone()[0]
```

Integrar en `core/engine.py`:

```python
from data.database import DatabaseManager

class Engine:
    def __init__(self, config: Dict[str, Any]):
        # ... código existente ...

        # Inicializar base de datos
        db_path = config['database']['path']
        self.db = DatabaseManager(db_path)

    def run(self) -> pd.DataFrame:
        # ... después de obtener datos ...

        # Guardar en base de datos
        self.logger.info("Guardando datos en base de datos...")
        self.db.save_ohlcv(df)

        return df
```

### 4. Implementar Alertas de Telegram

Primero, instalar la librería:

```bash
pip install python-telegram-bot
```

Actualizar `alerts/telegram.py`:

```python
from telegram import Bot
from telegram.error import TelegramError

class TelegramAlert:
    def __init__(self, bot_token: str, chat_id: str):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.logger = logging.getLogger(__name__)

        try:
            self.bot = Bot(token=bot_token)
            self.enabled = True
            self.logger.info("TelegramAlert inicializado correctamente")
        except Exception as e:
            self.logger.error(f"Error al inicializar Telegram: {e}")
            self.enabled = False

    def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Envía un mensaje a través de Telegram."""
        if not self.enabled:
            return False

        try:
            self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            self.logger.info("Mensaje enviado correctamente")
            return True
        except TelegramError as e:
            self.logger.error(f"Error al enviar mensaje: {e}")
            return False
```

Configurar en `config/settings.yaml`:

```yaml
alerts:
  telegram:
    enabled: true
    bot_token: "TU_BOT_TOKEN_AQUI"
    chat_id: "TU_CHAT_ID_AQUI"
```

---

## 🔄 Ejecutar como Servicio (Linux/Raspberry Pi)

### 1. Crear Servicio systemd

Crear archivo `/etc/systemd/system/kraken-bot.service`:

```ini
[Unit]
Description=Kraken Bot - Sistema de Lectura de Mercado
After=network.target

[Service]
Type=simple
User=tu_usuario
WorkingDirectory=/home/tu_usuario/kraken-bot
ExecStart=/home/tu_usuario/kraken-bot/.venv/bin/python main.py
Restart=always
RestartSec=60

[Install]
WantedBy=multi-user.target
```

### 2. Activar y Ejecutar

```bash
# Recargar systemd
sudo systemctl daemon-reload

# Habilitar servicio (arranque automático)
sudo systemctl enable kraken-bot

# Iniciar servicio
sudo systemctl start kraken-bot

# Ver estado
sudo systemctl status kraken-bot

# Ver logs
sudo journalctl -u kraken-bot -f
```

---

## 🧪 Testing

Crear pruebas unitarias en `tests/`:

```python
# tests/test_indicators.py
import pytest
import pandas as pd
from indicators import calculate_rsi

def test_calculate_rsi():
    """Test básico del cálculo de RSI."""
    # Crear datos de prueba
    df = pd.DataFrame({
        'close': [100, 102, 101, 103, 105, 104, 106, 108, 107, 109,
                  111, 110, 112, 114, 113, 115]
    })

    # Calcular RSI
    result = calculate_rsi(df, period=14)

    # Verificar que la columna existe
    assert 'rsi' in result.columns

    # Verificar que los valores están en el rango correcto
    rsi_values = result['rsi'].dropna()
    assert all(0 <= val <= 100 for val in rsi_values)

def test_rsi_insufficient_data():
    """Test con datos insuficientes."""
    df = pd.DataFrame({'close': [100, 102, 101]})

    with pytest.raises(ValueError):
        calculate_rsi(df, period=14)
```

Ejecutar tests:

```bash
pip install pytest pytest-cov
pytest tests/ -v --cov=.
```

---

## 📊 Monitoreo y Debugging

### Nivel de Logging

Ajustar en `config/settings.yaml`:

```yaml
logging:
  level: "DEBUG" # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Logs Detallados

Ver logs en tiempo real:

```bash
tail -f logs/bot.log
```

Filtrar errores:

```bash
grep ERROR logs/bot.log
```

---

## 🚀 Mejores Prácticas

1. **Nunca hardcodear valores**: Usar siempre `settings.yaml`
2. **Logging apropiado**: INFO para flujo normal, ERROR para problemas
3. **Manejo de excepciones**: Capturar y loggear errores específicos
4. **Type hints**: Usar anotaciones de tipo en funciones
5. **Documentación**: Mantener docstrings actualizados
6. **Testing**: Escribir tests para nueva funcionalidad
7. **Git**: Commits pequeños y descriptivos

---

## 📚 Recursos Adicionales

- **ccxt Documentation**: https://docs.ccxt.com/
- **Pandas Guide**: https://pandas.pydata.org/docs/
- **Kraken API**: https://docs.kraken.com/rest/
- **Python Logging**: https://docs.python.org/3/library/logging.html

---

**Fecha de actualización**: 2025-12-23
