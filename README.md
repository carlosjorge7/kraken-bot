# 🤖 Kraken Bot - Sistema de Lectura de Mercado

Bot profesional de lectura de datos del mercado de criptomonedas usando la API pública de Kraken.

> ⚠️ **IMPORTANTE**: Este bot NO realiza trading automático. Solo lee datos del mercado para análisis.

## 🎯 Objetivo

Construir una base sólida y profesional para:

- Leer datos OHLCV (velas) del mercado
- Procesar y analizar información de precios
- Servir como fundamento para indicadores y alertas futuras
- Preparado para ejecutarse 24/7 (Raspberry Pi, VPS, etc.)

## 📋 Características

- ✅ Conexión a Kraken usando API pública (sin credenciales)
- ✅ Descarga de datos OHLCV en formato estructurado
- ✅ Sistema de logging profesional con rotación de archivos
- ✅ Configuración centralizada en YAML
- ✅ Arquitectura modular y escalable
- ✅ Base de datos SQLite para almacenamiento (preparada)
- ✅ Módulo de indicadores técnicos (RSI implementado, listo para usar)
- ✅ Sistema de alertas preparado (stub para Telegram)

## 🏗️ Estructura del Proyecto

```
kraken-bot/
├── config/
│   └── settings.yaml          # Configuración central
├── data/
│   └── ohlcv.db               # Base de datos SQLite
├── fetcher/
│   └── kraken_client.py       # Cliente de Kraken (ccxt)
├── indicators/
│   └── rsi.py                 # Cálculo de RSI
├── alerts/
│   └── telegram.py            # Alertas (stub)
├── core/
│   └── engine.py              # Motor principal
├── logs/
│   └── bot.log                # Logs del sistema
├── main.py                    # Punto de entrada
└── README.md                  # Este archivo
```

## 🚀 Instalación

### 1. Requisitos

- Python 3.10 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar Dependencias

```bash
# Instalar librerías necesarias
pip install ccxt pandas pyyaml

# O usar requirements.txt (si existe)
pip install -r requirements.txt
```

### 3. Verificar Instalación

```bash
python -c "import ccxt, pandas, yaml; print('✓ Dependencias instaladas correctamente')"
```

## 📖 Uso

### Ejecución Básica

```bash
cd kraken-bot
python main.py
```

### Configuración

Edita `config/settings.yaml` para ajustar:

```yaml
exchange:
  symbol: "BTC/USD" # Par a monitorear
  timeframe: "15m" # 1m, 5m, 15m, 30m, 1h, 4h, 1d
  limit: 100 # Número de velas a descargar
```

### Ejemplo de Salida

```
======================================================================
  KRAKEN BOT - Sistema de Lectura de Mercado
======================================================================

📋 Cargando configuración...
✓ Configuración cargada exitosamente

📝 Configurando sistema de logging...
✓ Logging configurado

🔧 Configuración del bot:
   • Exchange:   Kraken
   • Par:        BTC/USD
   • Timeframe:  15m
   • Velas:      100

🚀 Inicializando motor del bot...
✓ Motor inicializado

📡 Conectando con Kraken y obteniendo datos...

[Logs detallados del proceso...]

✅ Proceso completado exitosamente
   • Se obtuvieron 100 velas
   • Último precio: $96,850.00

======================================================================
```

## 🔧 Módulos

### KrakenClient (`fetcher/kraken_client.py`)

Cliente para interactuar con Kraken:

- `fetch_ohlcv()`: Descarga datos OHLCV
- `check_connection()`: Verifica conectividad
- `get_exchange_info()`: Información del exchange

### Engine (`core/engine.py`)

Motor principal del sistema:

- Orquesta todos los componentes
- Procesa datos del mercado
- Muestra resúmenes y estadísticas
- Preparado para añadir indicadores y alertas

### Indicadores (`indicators/rsi.py`)

Cálculo de indicadores técnicos:

- `calculate_rsi()`: Calcula RSI
- `get_rsi_signal()`: Interpreta señales
- `analyze_rsi()`: Análisis completo

**Nota**: Implementado pero no usado aún en el flujo principal.

### Alertas (`alerts/telegram.py`)

Sistema de alertas (stub):

- `send_message()`: Envío de mensajes
- `send_price_alert()`: Alertas de precio
- `send_indicator_alert()`: Alertas de indicadores

**Nota**: Preparado para implementación futura.

## 📊 Próximos Pasos (Roadmap)

### Fase 1: Base (✅ COMPLETADO)

- [x] Estructura del proyecto
- [x] Conexión a Kraken
- [x] Descarga de OHLCV
- [x] Sistema de logging
- [x] Configuración YAML

### Fase 2: Almacenamiento (Próximo)

- [ ] Implementar guardado en SQLite
- [ ] Sistema de persistencia de datos
- [ ] Sincronización automática

### Fase 3: Análisis (Futuro)

- [ ] Integrar indicadores (RSI, MACD, etc.)
- [ ] Detección de señales
- [ ] Análisis de tendencias

### Fase 4: Alertas (Futuro)

- [ ] Implementar Telegram Bot
- [ ] Sistema de notificaciones
- [ ] Alertas configurables

### Fase 5: Producción (Futuro)

- [ ] Servicio systemd
- [ ] Deployment en Raspberry Pi
- [ ] Monitoreo 24/7
- [ ] Dashboard web (opcional)

## ⚠️ Limitaciones Actuales

- **Solo lectura**: No realiza trading ni envía órdenes
- **API pública**: No requiere credenciales (sin acceso a cuenta)
- **Sin persistencia**: Los datos no se guardan aún en la BD
- **Sin alertas**: El módulo de Telegram es un stub
- **Sin indicadores activos**: RSI implementado pero no integrado

## 🛡️ Seguridad

- ✅ No requiere API keys
- ✅ Solo usa endpoints públicos
- ✅ No puede realizar operaciones de trading
- ✅ Código auditable y transparente

## 📝 Logs

Los logs se guardan en `logs/bot.log` con rotación automática:

- Tamaño máximo: 10MB por archivo
- Archivos de backup: 5
- Nivel: INFO (configurable en settings.yaml)

## 🤝 Contribuir

Este es un proyecto base. Para extenderlo:

1. **Añadir indicadores**: Crea nuevos archivos en `indicators/`
2. **Integrar BD**: Implementa guardado en `data/ohlcv.db`
3. **Activar alertas**: Completa la implementación de `alerts/telegram.py`
4. **Crear estrategias**: Añade lógica de análisis en `core/engine.py`

## 📄 Licencia

Proyecto educativo y base para desarrollo personal.

## 📧 Contacto

Bot desarrollado como base profesional para trading algorítmico (solo lectura).

---

**Última actualización**: 2025-12-23
