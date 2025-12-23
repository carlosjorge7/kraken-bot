# 🚀 KRAKEN BOT - PRODUCCIÓN

Bot profesional de lectura de mercado 24/7. Sin fluff, solo lo esencial.

## Quick Start

```bash
# Un solo ciclo
python main.py --once

# Modo continuo (24/7)
python main.py --continuous
```

## Instalación Producción

### Linux/Raspberry Pi

```bash
# Clonar/copiar proyecto
cd /opt
sudo git clone <repo> kraken-bot

# Setup
cd kraken-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Configurar
nano config/settings.yaml

# Instalar servicio
sudo cp deploy/kraken-bot.service /etc/systemd/system/
sudo nano /etc/systemd/system/kraken-bot.service  # Ajustar paths
sudo systemctl daemon-reload
sudo systemctl enable kraken-bot
sudo systemctl start kraken-bot
```

### Comandos

```bash
# Estado
sudo systemctl status kraken-bot

# Logs
sudo journalctl -u kraken-bot -f

# Reiniciar
sudo systemctl restart kraken-bot

# Detener
sudo systemctl stop kraken-bot
```

## Configuración

`config/settings.yaml`:

```yaml
exchange:
  symbol: "BTC/USD"
  timeframe: "15m"
  limit: 100

scheduler:
  interval: 300 # 5 minutos entre ciclos
  max_retries: 3 # Reintentos en caso de error
  retry_delay: 60 # Segundos entre reintentos

database:
  path: "data/ohlcv.db"

logging:
  level: "INFO"
  file: "logs/bot.log"
```

## Características Producción

- ✅ **Base de datos SQLite** - Persistencia automática
- ✅ **Loop continuo** - Ejecución 24/7
- ✅ **Retry logic** - Reintentos automáticos
- ✅ **Graceful shutdown** - Manejo de SIGTERM/SIGINT
- ✅ **Systemd service** - Auto-restart, logs
- ✅ **Resource limits** - Control de memoria/CPU

## Base de Datos

```bash
# Ver datos
sqlite3 data/ohlcv.db "SELECT * FROM ohlcv ORDER BY timestamp DESC LIMIT 10;"

# Contar registros
sqlite3 data/ohlcv.db "SELECT COUNT(*) FROM ohlcv;"

# Backup
cp data/ohlcv.db data/ohlcv-$(date +%Y%m%d).db
```

## Monitoreo

```bash
# Logs en vivo
tail -f logs/bot.log

# Uso de recursos
top -p $(pgrep -f "python.*kraken-bot")

# Espacio en disco
du -sh data/
```

## Troubleshooting

### Bot no arranca

```bash
# Ver errores
sudo journalctl -u kraken-bot -xe

# Probar manual
cd /opt/kraken-bot
.venv/bin/python main.py --once
```

### Problemas de red

```bash
# Test conectividad
.venv/bin/python verificar_sistema.py
```

### BD bloqueada

```bash
# Ver procesos
lsof data/ohlcv.db

# Recrear
mv data/ohlcv.db data/ohlcv.db.old
```

## Estructura

```
kraken-bot/
├── main.py              # Punto de entrada
├── config/
│   └── settings.yaml    # Configuración
├── core/
│   └── engine.py        # Motor principal
├── fetcher/
│   └── kraken_client.py # Cliente Kraken (ccxt)
├── data/
│   ├── database.py      # SQLite manager
│   └── ohlcv.db         # Base de datos
├── indicators/
│   └── rsi.py           # RSI (listo para usar)
├── alerts/
│   └── telegram.py      # Telegram (stub)
├── deploy/
│   ├── kraken-bot.service  # Systemd service
│   └── deploy.sh           # Script instalación
└── logs/
    └── bot.log          # Logs
```

## API Usage

El bot usa `ccxt` para acceder a Kraken:

```python
import ccxt

exchange = ccxt.kraken()
ohlcv = exchange.fetch_ohlcv("BTC/USD", "15m", 100)
```

**NO se usa:**

- HTTP directo (requests, urllib)
- Firma de peticiones (hmac)
- API keys (solo endpoints públicos)

## Límites

- Exchange: Kraken
- Modo: Solo lectura (NO trading)
- API: Solo pública
- Dependencias: ccxt, pandas, pyyaml

## Raspberry Pi

```bash
# Optimizar
sudo raspi-config
# GPU Memory: 16MB
# Overclock: Opcional

# Limitar recursos en systemd
MemoryMax=256M
CPUQuota=50%
```

## Backup

```bash
tar -czf backup-$(date +%Y%m%d).tar.gz \
  config/ data/ logs/
```

---

**Modo:** Producción Ready  
**Estado:** Estable  
**24/7:** Sí
