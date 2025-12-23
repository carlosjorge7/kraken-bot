# 🚀 Guía de Deployment

## Instalación en Producción

### Opción 1: Script Automático

```bash
# Copiar proyecto al servidor
scp -r kraken-bot/ user@servidor:/tmp/

# Conectar al servidor
ssh user@servidor

# Ejecutar instalación
cd /tmp/kraken-bot
sudo chmod +x deploy/deploy.sh
sudo deploy/deploy.sh install
```

### Opción 2: Manual

```bash
# 1. Crear directorio
sudo mkdir -p /opt/kraken-bot

# 2. Copiar archivos
sudo cp -r . /opt/kraken-bot/

# 3. Crear entorno virtual
cd /opt/kraken-bot
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 4. Configurar
nano config/settings.yaml

# 5. Instalar servicio
sudo cp deploy/kraken-bot.service /etc/systemd/system/
sudo nano /etc/systemd/system/kraken-bot.service
# Editar paths y usuario

# 6. Activar
sudo systemctl daemon-reload
sudo systemctl enable kraken-bot
sudo systemctl start kraken-bot
```

## Comandos de Gestión

```bash
# Iniciar
sudo systemctl start kraken-bot

# Detener
sudo systemctl stop kraken-bot

# Reiniciar
sudo systemctl restart kraken-bot

# Ver estado
sudo systemctl status kraken-bot

# Ver logs
sudo journalctl -u kraken-bot -f

# Ver logs (últimas 100 líneas)
sudo journalctl -u kraken-bot -n 100

# Deshabilitar auto-inicio
sudo systemctl disable kraken-bot
```

## Ejecución Manual

```bash
# Un solo ciclo
python main.py --once

# Modo continuo
python main.py --continuous
```

## Monitoreo

### Ver logs en tiempo real

```bash
tail -f logs/bot.log
```

### Ver datos en BD

```bash
sqlite3 data/ohlcv.db "SELECT * FROM ohlcv ORDER BY timestamp DESC LIMIT 10;"
```

### Verificar espacio en disco

```bash
du -sh data/
```

## Actualización

```bash
# Con script
sudo deploy/deploy.sh update

# Manual
sudo systemctl stop kraken-bot
sudo cp -r /tmp/nuevo-codigo/* /opt/kraken-bot/
sudo systemctl start kraken-bot
```

## Troubleshooting

### Bot no inicia

```bash
# Ver errores
sudo journalctl -u kraken-bot -xe

# Verificar permisos
ls -la /opt/kraken-bot

# Probar manualmente
cd /opt/kraken-bot
.venv/bin/python main.py --once
```

### Problemas de red

```bash
# Verificar conectividad
.venv/bin/python -c "import ccxt; print(ccxt.kraken().fetch_ticker('BTC/USD'))"
```

### Base de datos bloqueada

```bash
# Verificar procesos
lsof data/ohlcv.db

# Backup y recrear
mv data/ohlcv.db data/ohlcv.db.bak
```

## Backup

```bash
# Backup completo
tar -czf kraken-bot-backup-$(date +%Y%m%d).tar.gz \
  /opt/kraken-bot/config/ \
  /opt/kraken-bot/data/ \
  /opt/kraken-bot/logs/
```

## Raspberry Pi

```bash
# Optimizaciones
sudo apt-get install python3-dev
sudo raspi-config
# Reducir GPU memory a 16MB

# Limitar recursos en systemd
sudo nano /etc/systemd/system/kraken-bot.service
# Añadir: MemoryMax=256M
```
