# 📦 Estructura del Backend Observer

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Aplicación FastAPI principal
│   ├── config.py                  # Configuración con Pydantic Settings
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes.py              # Endpoints REST
│   │   └── websocket.py           # Handler WebSocket
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   └── schemas.py             # Modelos Pydantic (Request/Response)
│   │
│   └── services/
│       ├── __init__.py
│       └── state_reader.py        # Servicio de lectura de estado
│
├── examples/
│   └── api_responses.json         # Ejemplos de respuestas JSON
│
├── start_observer.py              # Script de inicio
└── README.md                      # Documentación completa
```

## 🎯 Componentes Principales

### 1. **main.py** - Aplicación FastAPI

- Configura FastAPI con CORS
- Registra rutas REST
- Configura WebSocket endpoint
- Lifecycle events (startup/shutdown)

### 2. **config.py** - Configuración

- Settings con Pydantic
- Paths de archivos de estado
- Configuración de CORS
- Límites y timeouts

### 3. **routes.py** - Endpoints REST

- `GET /api/health` - Health check
- `GET /api/markets` - Lista de mercados
- `GET /api/status` - Estado de todos los mercados
- `GET /api/status/{symbol}` - Estado de un mercado
- `GET /api/alerts` - Alertas recientes

### 4. **websocket.py** - WebSocket Handler

- Gestión de conexiones
- Envío de alertas en tiempo real
- Heartbeat para mantener conexión
- Broadcast a múltiples clientes

### 5. **schemas.py** - Modelos Pydantic

- `HealthResponse`
- `MarketInfo`
- `MarketStatus`
- `Alert`
- `WSMessage`
- Enums (RSIState)

### 6. **state_reader.py** - Servicio de Lectura

- Lee `data/bot_state.json`
- Lee `data/alerts.json`
- Consulta BD (fallback)
- **NO ejecuta lógica de negocio**
- **NO calcula indicadores**

## 🔄 Flujo de Datos

```
┌─────────────────┐
│   Kraken Bot    │
│   (Engine)      │
└────────┬────────┘
         │
         │ Escribe estado
         ▼
┌─────────────────┐
│ bot_state.json  │
│ alerts.json     │
└────────┬────────┘
         │
         │ Lee estado
         ▼
┌─────────────────┐
│  StateReader    │
│   (Service)     │
└────────┬────────┘
         │
         │ Expone datos
         ▼
┌─────────────────┐
│  FastAPI        │
│  (REST + WS)    │
└────────┬────────┘
         │
         │ Consume
         ▼
┌─────────────────┐
│   Frontend      │
│ (React/Angular) │
└─────────────────┘
```

## 📝 Archivos de Estado

### `data/bot_state.json`

```json
{
  "markets": [...],
  "status": {
    "BTC/USD": {
      "timeframe": "15m",
      "last_price": 87894.10,
      "rsi_value": 45.32,
      "rsi_state": "NEUTRAL",
      "last_update": "2025-12-25T21:45:00",
      "data_available": true
    }
  }
}
```

### `data/alerts.json`

```json
{
  "alerts": [
    {
      "symbol": "ETH/USD",
      "rsi": 28.9,
      "state": "OVERSOLD",
      "timestamp": "2025-12-25T21:45:00",
      "message": "⚠️ RSI en sobreventa..."
    }
  ]
}
```

## 🚀 Comandos Rápidos

```bash
# Instalar dependencias
pip install -r requirements.txt

# Iniciar backend observer
cd backend
python start_observer.py

# O con uvicorn directamente
uvicorn backend.app.main:app --reload --port 8001

# Probar endpoints
curl http://localhost:8001/api/health
curl http://localhost:8001/api/markets
curl http://localhost:8001/api/status
curl http://localhost:8001/api/alerts
```

## 🔌 WebSocket Client Example

```javascript
const ws = new WebSocket("ws://localhost:8001/ws/alerts");

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch (data.type) {
    case "connected":
      console.log("✅ Conectado");
      break;
    case "alert":
      console.log("🚨 Nueva alerta:", data.alert);
      break;
    case "heartbeat":
      console.log("💓 Heartbeat");
      break;
  }
};
```

## ✅ Características

- ✅ **Solo lectura** - No modifica el sistema
- ✅ **Asíncrono** - Usa async/await
- ✅ **Documentado** - OpenAPI automático
- ✅ **CORS habilitado** - Listo para frontend
- ✅ **WebSocket** - Alertas en tiempo real
- ✅ **Type-safe** - Pydantic models
- ✅ **Escalable** - Arquitectura limpia

## ❌ Lo que NO hace

- ❌ NO llama a Kraken
- ❌ NO calcula RSI
- ❌ NO ejecuta el engine
- ❌ NO hace trading
- ❌ NO modifica datos
- ❌ NO tiene autenticación (todavía)

## 📚 Documentación

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc
- **README completo**: backend/README.md
