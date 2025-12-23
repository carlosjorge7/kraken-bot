# 🤖 Kraken Bot - Guía de Uso Local

## Instalación

```bash
cd kraken-bot
python3 -m venv .venv
source .venv/bin/activate  # En macOS/Linux
pip install -r requirements.txt
```

## Configuración

Edita `config/settings.yaml`:

```yaml
exchange:
  symbol: "BTC/USD" # Par a monitorear
  timeframe: "15m" # 1m, 5m, 15m, 30m, 1h, 4h, 1d
  limit: 100 # Número de velas

scheduler:
  interval: 300 # Segundos entre ciclos (300 = 5 min)
  max_retries: 3
  retry_delay: 60

database:
  path: "data/ohlcv.db"

logging:
  level: "INFO"
```

## Ejecución

### Un solo ciclo

```bash
python main.py --once
```

### Modo continuo (para dejar corriendo)

```bash
python main.py --continuous
```

Para detener: `Ctrl+C`

## Ver datos guardados

```bash
# Contar registros
sqlite3 data/ohlcv.db "SELECT COUNT(*) FROM ohlcv;"

# Ver últimos 10
sqlite3 data/ohlcv.db "SELECT timestamp, symbol, close FROM ohlcv ORDER BY timestamp DESC LIMIT 10;"

# Ver resumen
sqlite3 data/ohlcv.db "SELECT symbol, COUNT(*) as total, MIN(timestamp) as desde, MAX(timestamp) as hasta FROM ohlcv GROUP BY symbol;"
```

## Logs

```bash
# Ver logs en tiempo real
tail -f logs/bot.log

# Buscar errores
grep ERROR logs/bot.log
```

## Ver pares disponibles

```bash
# Todos los pares
python listar_pares.py

# Filtrar por moneda
python listar_pares.py --filter BTC
python listar_pares.py --filter ETH
```

## Verificar sistema

```bash
python verificar_sistema.py
```

## Ejemplo con RSI

```bash
python examples/ejemplo_rsi.py
```

## Troubleshooting

**Error de conexión:**

```bash
# Verificar internet
ping api.kraken.com

# Test manual
python -c "import ccxt; print(ccxt.kraken().fetch_ticker('BTC/USD'))"
```

**Base de datos bloqueada:**

```bash
# Ver procesos
lsof data/ohlcv.db

# Si está corrupta, renombrar
mv data/ohlcv.db data/ohlcv.db.old
```

## Estructura datos

La base de datos guarda:

- timestamp
- symbol (BTC/USD, ETH/USD, etc)
- open, high, low, close
- volume

## Siguientes pasos

1. Ejecuta `python main.py --once` para probar
2. Revisa los logs en `logs/bot.log`
3. Verifica datos en `data/ohlcv.db`
4. Cuando esté todo OK, usa `--continuous`

---

**Nota:** Los archivos en `deploy/` son para Raspberry Pi/servidor, ignóralos por ahora.
