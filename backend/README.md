# 🔭 Kraken Bot Observer API

**Backend FastAPI de solo lectura para observar el estado del sistema Kraken Bot.**

## 📋 Descripción

Este backend **NO ejecuta lógica de trading**. Es una capa de observación que:

- ✅ Lee el estado del sistema desde archivos JSON
- ✅ Expone datos de mercado (precio, RSI, estado)
- ✅ Proporciona alertas detectadas por el bot
- ✅ Ofrece WebSocket para alertas en tiempo real
- ❌ NO llama a Kraken
- ❌ NO calcula indicadores
- ❌ NO ejecuta el engine del bot

## 🏗️ Arquitectura

```
backend/
├── app/
│   ├── main.py              # Aplicación FastAPI principal
│   ├── config.py            # Configuración
│   ├── api/
│   │   ├── routes.py        # Endpoints REST
│   │   └── websocket.py     # Handler WebSocket
│   ├── models/
│   │   └── schemas.py       # Modelos Pydantic
│   └── services/
│       └── state_reader.py  # Servicio de lectura de estado
└── start_observer.py        # Script de inicio
```

## 🚀 Inicio Rápido

### 1. Instalar Dependencias

```bash
pip install fastapi uvicorn pydantic-settings websockets
```

### 2. Iniciar el Servidor

```bash
cd backend
python start_observer.py
```

O directamente con uvicorn:

```bash
uvicorn backend.app.main:app --host 0.0.0.0 --port 8001 --reload
```

### 3. Acceder a la Documentación

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **WebSocket**: ws://localhost:8001/ws/alerts

## 📡 Endpoints

### `GET /api/health`

Health check del servicio.

**Respuesta:**

```json
{
  "status": "ok",
  "timestamp": "2025-12-25T22:00:00"
}
```

### `GET /api/markets`

Lista de mercados monitoreados.

**Respuesta:**

```json
{
  "markets": [
    {
      "symbol": "BTC/USD",
      "timeframe": "15m"
    },
    {
      "symbol": "ETH/USD",
      "timeframe": "15m"
    }
  ],
  "total": 2
}
```

### `GET /api/status`

Estado actual de todos los mercados.

**Respuesta:**

```json
{
  "markets": [
    {
      "symbol": "BTC/USD",
      "timeframe": "15m",
      "last_price": 87894.1,
      "rsi_value": 45.32,
      "rsi_state": "NEUTRAL",
      "last_update": "2025-12-25T21:45:00",
      "data_available": true
    },
    {
      "symbol": "ETH/USD",
      "timeframe": "15m",
      "last_price": 2945.94,
      "rsi_value": 28.9,
      "rsi_state": "OVERSOLD",
      "last_update": "2025-12-25T21:45:00",
      "data_available": true
    }
  ],
  "timestamp": "2025-12-25T22:00:00"
}
```

### `GET /api/status/{symbol}`

Estado de un mercado específico.

**Ejemplo:**

```bash
curl http://localhost:8001/api/status/BTC-USD
```

### `GET /api/alerts?limit=50`

Alertas recientes detectadas por el bot.

**Respuesta:**

```json
{
  "alerts": [
    {
      "id": 0,
      "symbol": "ETH/USD",
      "rsi": 28.9,
      "state": "OVERSOLD",
      "timestamp": "2025-12-25T21:45:00",
      "message": "⚠️ RSI en sobreventa: ETH/USD | RSI 28.9 | 15m"
    },
    {
      "id": 1,
      "symbol": "BTC/USD",
      "rsi": 72.3,
      "state": "OVERBOUGHT",
      "timestamp": "2025-12-25T22:15:00",
      "message": "⚠️ RSI en sobrecompra: BTC/USD | RSI 72.3 | 15m"
    }
  ],
  "total": 2,
  "last_update": "2025-12-25T22:15:00"
}
```

## 🔌 WebSocket

### Conexión

```javascript
const ws = new WebSocket("ws://localhost:8001/ws/alerts");

ws.onopen = () => {
  console.log("Conectado al sistema de alertas");
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  if (data.type === "alert") {
    console.log("Nueva alerta:", data.alert);
  } else if (data.type === "heartbeat") {
    console.log("Heartbeat recibido");
  }
};
```

### Mensajes Recibidos

**Conexión exitosa:**

```json
{
  "type": "connected",
  "message": "Conectado al sistema de alertas",
  "timestamp": "2025-12-25T22:00:00"
}
```

**Nueva alerta:**

```json
{
  "type": "alert",
  "alert": {
    "id": 5,
    "symbol": "BTC/USD",
    "rsi": 72.5,
    "state": "OVERBOUGHT",
    "timestamp": "2025-12-25T22:30:00",
    "message": "⚠️ RSI en sobrecompra: BTC/USD | RSI 72.5 | 15m"
  },
  "timestamp": "2025-12-25T22:30:01"
}
```

**Heartbeat:**

```json
{
  "type": "heartbeat",
  "timestamp": "2025-12-25T22:00:30"
}
```

## 📁 Archivos de Estado

El backend lee información desde estos archivos (generados por el bot):

### `data/bot_state.json`

Estado actual del sistema:

```json
{
  "markets": [
    { "symbol": "BTC/USD", "timeframe": "15m" },
    { "symbol": "ETH/USD", "timeframe": "15m" }
  ],
  "status": {
    "BTC/USD": {
      "timeframe": "15m",
      "last_price": 87894.1,
      "rsi_value": 45.32,
      "rsi_state": "NEUTRAL",
      "last_update": "2025-12-25T21:45:00",
      "data_available": true
    },
    "ETH/USD": {
      "timeframe": "15m",
      "last_price": 2945.94,
      "rsi_value": 28.9,
      "rsi_state": "OVERSOLD",
      "last_update": "2025-12-25T21:45:00",
      "data_available": true
    }
  }
}
```

### `data/alerts.json`

Historial de alertas:

```json
{
  "alerts": [
    {
      "symbol": "ETH/USD",
      "rsi": 28.9,
      "state": "OVERSOLD",
      "timestamp": "2025-12-25T21:45:00",
      "message": "⚠️ RSI en sobreventa: ETH/USD | RSI 28.9 | 15m"
    }
  ]
}
```

## 🔧 Configuración

Editar `backend/app/config.py`:

```python
class Settings(BaseSettings):
    # API Settings
    API_TITLE: str = "Kraken Bot Observer API"
    API_VERSION: str = "1.0.0"

    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # Cambiar en producción

    # Database
    DATABASE_PATH: str = "data/ohlcv.db"

    # State Files
    STATE_FILE: str = "data/bot_state.json"
    ALERTS_FILE: str = "data/alerts.json"

    # Limits
    MAX_ALERTS_HISTORY: int = 100
```

## 🔗 Integración con el Bot

Para que el bot actualice el estado, agregar en `core/engine.py`:

```python
from backend.app.services.state_reader import state_reader

# En _display_market_summary, después de calcular RSI:
state_reader.update_state(symbol, {
    "timeframe": self.timeframe,
    "last_price": float(latest['close']),
    "rsi_value": rsi_value if rsi_value else None,
    "rsi_state": rsi_signal if rsi_signal else None,
    "last_update": str(latest['timestamp']),
    "data_available": True
})

# En _process_rsi_alert, cuando se detecta una alerta:
if alert_triggered:
    state_reader.add_alert({
        "symbol": symbol,
        "rsi": rsi_value,
        "state": current_state,
        "message": f"⚠️ RSI en {current_state.lower()}: {symbol} | RSI {rsi_value:.1f} | {self.timeframe}"
    })
```

## 📊 Ejemplos de Uso

### Python (requests)

```python
import requests

# Health check
response = requests.get("http://localhost:8001/api/health")
print(response.json())

# Obtener estado de mercados
response = requests.get("http://localhost:8001/api/status")
data = response.json()
for market in data['markets']:
    print(f"{market['symbol']}: ${market['last_price']} | RSI {market['rsi_value']} ({market['rsi_state']})")

# Obtener alertas
response = requests.get("http://localhost:8001/api/alerts?limit=10")
alerts = response.json()['alerts']
for alert in alerts:
    print(f"[{alert['timestamp']}] {alert['message']}")
```

### JavaScript (fetch)

```javascript
// Obtener estado
fetch("http://localhost:8001/api/status")
  .then((res) => res.json())
  .then((data) => {
    data.markets.forEach((market) => {
      console.log(
        `${market.symbol}: $${market.last_price} | RSI ${market.rsi_value}`
      );
    });
  });

// Obtener alertas
fetch("http://localhost:8001/api/alerts?limit=5")
  .then((res) => res.json())
  .then((data) => {
    data.alerts.forEach((alert) => {
      console.log(alert.message);
    });
  });
```

### cURL

```bash
# Health check
curl http://localhost:8001/api/health

# Mercados
curl http://localhost:8001/api/markets

# Estado
curl http://localhost:8001/api/status | jq .

# Alertas
curl http://localhost:8001/api/alerts?limit=10 | jq .
```

## 🐛 Troubleshooting

### Error: "Address already in use"

El puerto 8001 está ocupado. Cambiar puerto en `start_observer.py`:

```python
uvicorn.run(..., port=8002)
```

### Error: "File not found: data/bot_state.json"

Los archivos se crean automáticamente. Si el bot no los ha generado aún, el API retornará datos vacíos.

### WebSocket se desconecta

Normal si no hay actividad. El heartbeat mantiene la conexión viva.

## 📝 Notas Importantes

- ⚠️ Este backend **NO controla el bot**
- ⚠️ **NO ejecuta trading**
- ⚠️ **NO calcula indicadores**
- ✅ Solo **lee y expone** información
- ✅ Perfecto para **dashboards** y **frontends**
- ✅ Listo para **React, Angular, Vue, etc.**

## 📄 Licencia

Mismo que el proyecto principal kraken-bot.
