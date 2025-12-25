# 🤖 Kraken Bot - Sistema de Análisis de Mercado con RSI

Sistema profesional de monitoreo de criptomonedas con análisis técnico RSI y alertas automáticas. Usa la API pública de Kraken y expone una API REST para consulta de datos.

> ⚠️ **IMPORTANTE**: Este bot NO realiza trading automático. Solo analiza el mercado y genera alertas.

## 🎯 ¿Qué hace este sistema?

### 📊 Análisis Continuo del Mercado

- **Monitorea** BTC/USD y ETH/USD en tiempo real (cada 15 minutos)
- **Calcula RSI** (Relative Strength Index) automáticamente
- **Detecta señales** de sobrecompra (>70) y sobreventa (<30)
- **Genera alertas** cuando el RSI cruza a zonas extremas

### 🔌 API REST Completa

- Consulta precios actuales y datos históricos
- Accede a valores de RSI en tiempo real
- Revisa alertas generadas
- WebSocket para notificaciones en vivo

### 💾 Almacenamiento Persistente

- Guarda datos OHLCV en SQLite
- Mantiene historial de alertas en JSON
- Estado del sistema actualizado en tiempo real

### ⚡ Ejecución 24/7

- Listo para Raspberry Pi, VPS o cualquier servidor
- Un solo comando para levantar todo el sistema
- Gestión automática de ciclos y reintentos

## 📋 Características Implementadas

### 🔌 Core del Sistema

- ✅ Conexión a Kraken usando API pública (sin credenciales)
- ✅ Descarga de datos OHLCV cada 15 minutos
- ✅ Sistema de logging profesional con rotación de archivos
- ✅ Configuración centralizada en YAML
- ✅ Arquitectura modular y escalable

### 📊 Análisis Técnico

- ✅ **RSI (14 períodos)** calculado y funcionando
- ✅ **Detección de señales**: NEUTRAL, OVERBOUGHT, OVERSOLD
- ✅ **Sistema de alertas** con detección de cruces
- ✅ Base de datos SQLite con historial completo

### 🌐 API REST

- ✅ FastAPI con documentación Swagger
- ✅ Endpoints para markets, status, alerts
- ✅ WebSocket para alertas en tiempo real
- ✅ CORS habilitado para frontends

### 🚀 Deployment

- ✅ Sistema unificado (Bot + API en un solo proceso)
- ✅ Thread management para ejecución paralela
- ✅ Graceful shutdown y manejo de errores
- ✅ Listo para producción 24/7

## 🏗️ Estructura del Proyecto

```
kraken-bot/
├── config/
│   └── settings.yaml          # Configuración central
├── data/
│   ├── ohlcv.db               # Base de datos SQLite
│   ├── bot_state.json         # Estado del sistema
│   └── alerts.json            # Alertas generadas
├── fetcher/
│   └── kraken_client.py       # Cliente de Kraken (ccxt)
├── indicators/
│   └── rsi.py                 # Cálculo de RSI
├── core/
│   └── engine.py              # Motor principal del bot
├── backend/                    # API REST
│   ├── start_observer.py      # ⭐ Punto de entrada principal
│   └── app/
│       ├── main.py            # FastAPI app
│       ├── config.py          # Configuración API
│       ├── api/
│       │   ├── routes.py      # Endpoints REST
│       │   └── websocket.py   # WebSocket handler
│       ├── models/
│       │   └── schemas.py     # Modelos Pydantic
│       └── services/
│           └── state_reader.py # Lector de estado
├── logs/
│   └── bot.log                # Logs del sistema
├── main.py                    # Bot standalone (opcional)
├── requirements.txt           # Dependencias Python
└── README.md                  # Este archivo
```

## 🚀 Instalación

### 1. Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### 2. Clonar y preparar entorno

```bash
cd kraken-bot
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar (Opcional)

Edita `config/settings.yaml` si quieres cambiar los pares o intervalos:

```yaml
exchange:
  symbols:
    - "BTC/USD"
    - "ETH/USD"
  timeframe: "15m" # 1m, 5m, 15m, 30m, 1h, 4h, 1d
  limit: 100

scheduler:
  interval: 300 # Segundos entre ciclos (300 = 5 min)
```

## 📖 Uso

### 🚀 Inicio Rápido (Recomendado)

**Un solo comando levanta todo el sistema:**

```bash
python backend/start_observer.py
```

Esto iniciará:

- ✅ Bot de análisis en segundo plano (modo continuo)
- ✅ API REST en http://localhost:8001
- ✅ Documentación Swagger en http://localhost:8001/docs
- ✅ WebSocket en ws://localhost:8001/ws/alerts

### 🌐 Usar la API

**Swagger UI (Interfaz interactiva):**

```
http://localhost:8001/docs
```

**Ejemplos de endpoints:**

```bash
# Ver mercados monitoreados
curl http://localhost:8001/api/markets

# Ver estado actual (precios y RSI)
curl http://localhost:8001/api/status

# Ver alertas generadas
curl http://localhost:8001/api/alerts

# Health check
curl http://localhost:8001/api/health
```

### 🤖 Modo Bot Standalone (Alternativo)

Si solo quieres ejecutar el bot sin la API:

```bash
# Un solo ciclo
python main.py --once

# Modo continuo (24/7)
python main.py --continuous
```

### 📊 Ejemplo de Salida del Bot

```
============================================================
CICLO #1
============================================================

📊 RESUMEN: BTC/USD
------------------------------------------------------------
Timeframe:        15m
Total de velas:   100

💰 ÚLTIMA VELA (2025-12-25 22:15:00)
  Cierre:         $87,793.20
  Volumen:        1.0086

📈 ESTADÍSTICAS DEL PERIODO
  Precio mínimo:  $87,227.10
  Precio máximo:  $88,547.90
  Cambio:         $+143.20 (+0.16%)

📉 RSI (14): 45.20 → NEUTRAL

BD: 2 nuevas | Total BTC/USD: 204
============================================================
```

### ⚠️ Ejemplo de Alerta RSI

Cuando el RSI cruza a zona extrema:

```
⚠️ RSI en sobreventa: BTC/USD | RSI 28.5 | 15m
```

La alerta se guarda en:

- `data/alerts.json` (archivo)
- API REST: `GET /api/alerts`
- WebSocket en tiempo real

## 🔧 Arquitectura del Sistema

### 🤖 Bot (`core/engine.py`)

**Motor principal del análisis:**

- ✅ Ejecuta ciclos continuos cada 5 minutos
- ✅ Obtiene datos OHLCV de Kraken
- ✅ Calcula RSI (14 períodos) automáticamente
- ✅ Detecta cruces de RSI a zonas extremas
- ✅ Genera y guarda alertas en JSON
- ✅ Actualiza estado del sistema en tiempo real
- ✅ Guarda historial en SQLite

**Flujo de ejecución:**

```
1. Conectar con Kraken
2. Obtener datos OHLCV (100 velas)
3. Calcular RSI
4. Detectar señales (NEUTRAL/OVERBOUGHT/OVERSOLD)
5. Generar alertas si hay cruces
6. Guardar en BD y archivos de estado
7. Esperar hasta próximo ciclo
```

### 🌐 API REST (`backend/app/main.py`)

**FastAPI que expone datos del bot:**

- ✅ Lee estado desde `data/bot_state.json`
- ✅ Lee alertas desde `data/alerts.json`
- ✅ Lee historial desde SQLite
- ✅ Ejecuta el bot en thread separado
- ✅ WebSocket para notificaciones en vivo

**Endpoints disponibles:**

| Endpoint               | Método | Descripción                           |
| ---------------------- | ------ | ------------------------------------- |
| `/api/markets`         | GET    | Lista de mercados monitoreados        |
| `/api/status`          | GET    | Precios y RSI actuales                |
| `/api/status/{symbol}` | GET    | Estado de un mercado específico       |
| `/api/alerts`          | GET    | Alertas generadas (con paginación)    |
| `/api/health`          | GET    | Health check del sistema              |
| `/ws/alerts`           | WS     | WebSocket para alertas en tiempo real |

### 📊 Indicadores (`indicators/rsi.py`)

**Cálculo de RSI integrado:**

- ✅ `calculate_rsi()`: RSI basado en pandas
- ✅ `get_rsi_signal()`: Interpreta valores (>70, <30)
- ✅ Usado activamente en cada ciclo del bot

### 🔌 Cliente Kraken (`fetcher/kraken_client.py`)

**Interfaz con la API de Kraken:**

- ✅ `fetch_ohlcv()`: Descarga velas del mercado
- ✅ `check_connection()`: Verifica conectividad
- ✅ Manejo de errores y rate limiting

### 💾 Base de Datos (`data/database.py`)

**Persistencia en SQLite:**

- ✅ Guarda OHLCV con timestamp
- ✅ Evita duplicados automáticamente
- ✅ Consultas por símbolo y fecha

### 📁 Archivos de Estado

**Compartidos entre Bot y API:**

```json
// data/bot_state.json
{
  "markets": [{"symbol": "BTC/USD", "timeframe": "15m"}],
  "status": {
    "BTC/USD": {
      "last_price": 87793.2,
      "rsi_value": 45.2,
      "rsi_state": "NEUTRAL",
      "last_update": "2025-12-25T23:28:52"
    }
  }
}

// data/alerts.json
{
  "alerts": [{
    "symbol": "BTC/USD",
    "type": "rsi_oversold",
    "message": "RSI en sobreventa: BTC/USD | RSI 28.5 | 15m",
    "rsi_value": 28.5,
    "timestamp": "2025-12-25T23:30:00"
  }]
}
```

## 📊 Estado del Proyecto

### ✅ Fase 1: Base (COMPLETADO)

- [x] Estructura del proyecto
- [x] Conexión a Kraken
- [x] Descarga de OHLCV
- [x] Sistema de logging
- [x] Configuración YAML

### ✅ Fase 2: Almacenamiento (COMPLETADO)

- [x] Guardado en SQLite implementado
- [x] Sistema de persistencia de datos
- [x] Archivos JSON para estado compartido
- [x] Sincronización automática

### ✅ Fase 3: Análisis (COMPLETADO)

- [x] RSI integrado y funcionando
- [x] Detección de señales (OVERBOUGHT/OVERSOLD/NEUTRAL)
- [x] Detección de cruces para alertas
- [x] Análisis cada 15 minutos

### ✅ Fase 4: Alertas (COMPLETADO - Sistema Base)

- [x] Sistema de alertas funcionando
- [x] Guardado de alertas en JSON
- [x] API REST para consultar alertas
- [x] WebSocket para notificaciones en tiempo real
- [ ] Telegram Bot (pendiente - stub preparado)

### ✅ Fase 5: API REST (COMPLETADO)

- [x] FastAPI con documentación Swagger
- [x] Endpoints para markets, status, alerts
- [x] WebSocket para tiempo real
- [x] Sistema unificado (Bot + API)
- [x] Thread management

### 🚀 Próximos Pasos

- [ ] Implementar notificaciones por Telegram
- [ ] Añadir más indicadores (MACD, Bollinger Bands)
- [ ] Dashboard web con gráficas
- [ ] Servicio systemd para producción
- [ ] Docker container
- [ ] Tests automatizados

## ⚠️ Limitaciones y Consideraciones

### ✅ Funcional

- **Solo análisis**: No realiza trading ni envía órdenes (por diseño)
- **API pública**: No requiere credenciales de Kraken
- **RSI integrado**: Cálculo automático cada ciclo
- **Alertas funcionando**: Sistema de detección de cruces activo
- **Persistencia completa**: SQLite + archivos JSON

### 🔄 En Desarrollo

- **Telegram**: El módulo está preparado pero no implementado
- **Un solo indicador**: Solo RSI por ahora (fácil añadir más)
- **Timeframe fijo**: 15 minutos (configurable en settings.yaml)

### 🎯 Por Diseño

- **No trading**: Sistema de solo lectura y análisis
- **Datos públicos**: No accede a balance ni órdenes
- **Sin backtesting**: Enfocado en tiempo real

## 🛡️ Seguridad

- ✅ No requiere API keys
- ✅ Solo usa endpoints públicos
- ✅ No puede realizar operaciones de trading
- ✅ Código auditable y transparente

## 📝 Logs y Monitoreo

### 📄 Archivos de Log

Los logs se guardan en `logs/bot.log` con rotación automática:

- Tamaño máximo: 10MB por archivo
- Archivos de backup: 5
- Nivel: INFO (configurable en settings.yaml)

### 🔍 Ver logs en tiempo real

```bash
# Seguir el log del bot
tail -f logs/bot.log

# Ver solo alertas
grep "⚠️" logs/bot.log

# Ver errores
grep "ERROR" logs/bot.log
```

### 📊 Monitorear el sistema

```bash
# Health check de la API
curl http://localhost:8001/api/health

# Ver estado actual
curl http://localhost:8001/api/status | jq

# Ver últimas 10 alertas
curl http://localhost:8001/api/alerts?limit=10 | jq
```

## 🛠️ Extender el Sistema

### 📊 Añadir Nuevos Indicadores

1. Crea tu indicador en `indicators/mi_indicador.py`:

```python
def calculate_macd(df, fast=12, slow=26, signal=9):
    # Tu implementación
    return df
```

2. Impórtalo en `core/engine.py`:

```python
from indicators.mi_indicador import calculate_macd
```

3. Úsalo en `_display_market_summary()`

### 🔔 Implementar Telegram

1. Crea un bot con @BotFather en Telegram
2. Obtén tu token y chat_id
3. Implementa `alerts/telegram.py`:

```python
import requests

def send_alert(message):
    url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
    requests.post(url, json={"chat_id": CHAT_ID, "text": message})
```

4. Llama a `send_alert()` en `_process_rsi_alert()`

### 🎨 Crear un Frontend

La API está lista para consumirse desde cualquier frontend:

```javascript
// React, Vue, o vanilla JS
fetch("http://localhost:8001/api/status")
  .then((r) => r.json())
  .then((data) => console.log(data));
```

### 🐳 Dockerizar

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "backend/start_observer.py"]
```

## 🎓 Aprendizaje

Este proyecto demuestra:

- ✅ Integración con APIs de exchanges de crypto
- ✅ Análisis técnico con indicadores (RSI)
- ✅ Sistema de alertas basado en eventos
- ✅ API REST con FastAPI
- ✅ WebSockets para tiempo real
- ✅ Thread management en Python
- ✅ Persistencia con SQLite y JSON
- ✅ Arquitectura modular y escalable

## 📄 Licencia

Proyecto educativo para análisis de mercado.

## 🌟 Características Destacadas

- 🚀 **Un solo comando** levanta todo el sistema
- 📊 **RSI automático** cada 15 minutos
- 🔔 **Alertas inteligentes** con detección de cruces
- 🌐 **API REST completa** con Swagger
- ⚡ **WebSocket** para notificaciones en vivo
- 💾 **Persistencia dual**: SQLite + JSON
- 🔄 **Ejecución 24/7** lista para producción

---

**Última actualización**: 2025-12-25  
**Estado**: ✅ Sistema funcional y operativo
