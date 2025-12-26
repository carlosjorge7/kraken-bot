# 🔮 Módulo Predictivo - Predicción Probabilística de Dirección

## ⚠️ QUÉ ES Y QUÉ NO ES

### ✅ LO QUE SÍ ES:

- **Predicción de dirección** (UP/DOWN/NEUTRAL)
- **Probabilístico** con nivel de confianza (0.0 - 1.0)
- **Basado en reglas técnicas** explicables y auditables
- **Sin Machine Learning** (solo análisis técnico)
- **Complemento al sistema existente** (no rompe nada)

### ❌ LO QUE NO ES:

- NO predice precio exacto
- NO usa redes neuronales
- NO hace trading automático
- NO reemplaza análisis humano
- NO garantiza éxito en trading

---

## 🎯 OBJETIVO

Responder preguntas como:

- ¿Es más probable que el precio SUBA o BAJE en las próximas N velas?
- ¿Con qué nivel de confianza?
- ¿Por qué razones?

---

## 📊 EJEMPLO DE SALIDA

```json
{
  "symbol": "BTC/USD",
  "timeframe": "15m",
  "prediction": {
    "direction": "UP",
    "confidence": 0.63,
    "horizon": "next_3_candles",
    "quality": "MEDIUM",
    "reasons": [
      "RSI en sobreventa (28.5) - probable rebote",
      "RSI con tendencia alcista",
      "Momentum de precio positivo"
    ],
    "technical_scores": {
      "rsi_signal": 0.65,
      "rsi_momentum": 0.42,
      "price_momentum": 0.38,
      "volume_trend": 0.51
    },
    "timestamp": "2025-12-26T16:00:00"
  }
}
```

---

## 🧮 METODOLOGÍA

### 1. Señales Técnicas Analizadas

El predictor analiza **4 señales técnicas** y las combina con pesos:

| Señal              | Peso | Descripción                                       |
| ------------------ | ---- | ------------------------------------------------- |
| **RSI Signal**     | 35%  | Posición del RSI (sobreventa/sobrecompra/neutral) |
| **RSI Momentum**   | 20%  | Tendencia del RSI (subiendo/bajando)              |
| **Price Momentum** | 25%  | Momentum del precio reciente                      |
| **Volume Trend**   | 20%  | Tendencia del volumen confirmando dirección       |

### 2. Scoring System

Cada señal genera un **score entre -1.0 y +1.0**:

- **+1.0**: Muy alcista
- **0.0**: Neutral
- **-1.0**: Muy bajista

### 3. Combinación de Scores

Los scores se combinan usando los pesos:

```
Score Final = (RSI Signal × 0.35) + (RSI Momentum × 0.20) +
              (Price Momentum × 0.25) + (Volume Trend × 0.20)
```

### 4. Conversión a Predicción

El score final se convierte en dirección y confianza:

- **Score > +0.3**: Dirección UP (confianza proporcional)
- **Score < -0.3**: Dirección DOWN (confianza proporcional)
- **Score entre -0.3 y +0.3**: NEUTRAL (baja confianza)

---

## 🔍 DETALLE DE CADA SEÑAL

### 1. RSI Signal (35% del peso)

Analiza la **posición actual del RSI**:

```
RSI ≤ 20  → Score: +1.0 (sobreventa extrema)
RSI ≤ 30  → Score: +0.5 a +1.0
RSI 30-40 → Score: 0.0 a +0.5 (moderadamente alcista)
RSI 40-60 → Score: 0.0 (neutral)
RSI 60-70 → Score: 0.0 a -0.5 (moderadamente bajista)
RSI ≥ 70  → Score: -0.5 a -1.0
RSI ≥ 80  → Score: -1.0 (sobrecompra extrema)
```

**Lógica**: Cuando el RSI está en sobreventa, es probable un rebote (alcista). En sobrecompra, probable corrección (bajista).

### 2. RSI Momentum (20% del peso)

Analiza la **tendencia del RSI** (últimas 3 velas):

```python
rsi_change = RSI[-1] - RSI[-3]
score = tanh(rsi_change / 10)  # Normalizado
```

- **RSI subiendo** → Score positivo (alcista)
- **RSI bajando** → Score negativo (bajista)

**Lógica**: Si el RSI está ganando fuerza (subiendo), sugiere momentum alcista.

### 3. Price Momentum (25% del peso)

Analiza el **cambio de precio reciente** (últimas 5 velas):

```python
# Factor 1: Cambio porcentual
price_change_pct = (Close[-1] - Close[-5]) / Close[-5]
momentum_score = tanh(price_change_pct × 100) × 0.7

# Factor 2: Posición del cierre en la última vela
close_position = (Close - Low) / (High - Low)
candle_score = (close_position - 0.5) × 2 × 0.3

score = momentum_score + candle_score
```

**Lógica**: Precio subiendo + cierre cerca del máximo = alcista. Precio bajando + cierre cerca del mínimo = bajista.

### 4. Volume Trend (20% del peso)

Analiza la **confirmación por volumen**:

```python
recent_vol = promedio(Volumen últimas 5 velas)
older_vol = promedio(Volumen anteriores 5 velas)

vol_change = (recent_vol - older_vol) / older_vol
price_direction = +1 si precio sube, -1 si baja

if vol_change > 0.2:  # Volumen aumentó significativamente
    score = price_direction × 0.7
elif vol_change < -0.2:  # Volumen cayó
    score = 0.0  # Señal débil
else:
    score = price_direction × 0.3
```

**Lógica**: Volumen creciente confirmando dirección = señal fuerte. Volumen bajo = señal débil.

---

## 📈 NIVELES DE CONFIANZA

| Confianza | Calidad    | Interpretación                                   |
| --------- | ---------- | ------------------------------------------------ |
| 0.7 - 1.0 | **HIGH**   | Señal muy clara, múltiples indicadores alineados |
| 0.5 - 0.7 | **MEDIUM** | Señal moderada, algunos indicadores alineados    |
| 0.0 - 0.5 | **LOW**    | Señal débil o mixta, indicadores no alineados    |

---

## 🔧 CONFIGURACIÓN

En `config/settings.yaml`:

```yaml
predictions:
  # Activar/desactivar capa predictiva
  enabled: true

  # Horizonte temporal por defecto
  default_horizon: "next_3_candles"

  # Umbral mínimo de confianza
  min_confidence: 0.5

  # Pesos de cada señal (deben sumar 1.0)
  weights:
    rsi_signal: 0.35
    rsi_momentum: 0.20
    price_momentum: 0.25
    volume_trend: 0.20
```

---

## 🚀 USO

### Desde el Engine (automático)

El predictor se integra automáticamente en el engine:

```python
# El engine genera predicciones en cada ciclo si está habilitado
# Se guardan en data/bot_state.json junto con RSI y precio
```

### Endpoints REST

```bash
# Obtener predicciones de todos los mercados
GET http://localhost:8001/api/predictions

# Obtener predicción de un mercado específico
GET http://localhost:8001/api/predictions/BTC/USD
```

### Programáticamente

```python
from predictive.predictor import DirectionalPredictor, Horizon
import pandas as pd

# Crear predictor
predictor = DirectionalPredictor(rsi_period=14)

# Generar predicción
prediction = predictor.predict(
    df=ohlcv_dataframe,
    rsi_series=rsi_series,
    horizon=Horizon.NEXT_3_CANDLES
)

print(f"Dirección: {prediction.direction}")
print(f"Confianza: {prediction.confidence:.2%}")
print(f"Razones: {prediction.reasons}")
```

---

## ⚙️ HORIZONTES TEMPORALES

```python
class Horizon(str, Enum):
    NEXT_1_CANDLE = "next_1_candle"   # Próxima vela
    NEXT_3_CANDLES = "next_3_candles" # Próximas 3 velas (default)
    NEXT_5_CANDLES = "next_5_candles" # Próximas 5 velas
```

El horizonte es **informativo**, no cambia el cálculo (aún).

---

## 🎓 INTERPRETACIÓN DE RESULTADOS

### Ejemplo 1: Alta Confianza Alcista

```json
{
  "direction": "UP",
  "confidence": 0.82,
  "quality": "HIGH",
  "reasons": [
    "RSI en sobreventa (25.3) - probable rebote",
    "RSI con tendencia alcista",
    "Momentum de precio positivo (+2.5%)",
    "Volumen creciente confirmando tendencia (+35%)"
  ]
}
```

**Interpretación**: Múltiples señales apuntan a rebote alcista. RSI sobreventa + momentum positivo + volumen confirmando.

### Ejemplo 2: Confianza Media Bajista

```json
{
  "direction": "DOWN",
  "confidence": 0.58,
  "quality": "MEDIUM",
  "reasons": [
    "RSI alto (68.5) con riesgo de caída",
    "RSI con tendencia bajista",
    "Momentum de precio negativo (-1.2%)"
  ]
}
```

**Interpretación**: Señales moderadas de corrección. RSI cerca de sobrecompra, perdiendo fuerza.

### Ejemplo 3: Neutral

```json
{
  "direction": "NEUTRAL",
  "confidence": 0.35,
  "quality": "LOW",
  "reasons": ["Señales técnicas mixtas o débiles"]
}
```

**Interpretación**: No hay tendencia clara. Esperar confirmación antes de actuar.

---

## ⚠️ LIMITACIONES

1. **Solo análisis técnico**: No considera noticias, fundamentales, eventos macro
2. **Basado en datos históricos**: El pasado no garantiza el futuro
3. **Timeframe dependiente**: Funciona mejor con datos suficientes (>50 velas)
4. **No considera liquidez**: No analiza order book ni spreads
5. **Sin stop-loss**: NO incluye gestión de riesgo

---

## 🔬 VALIDACIÓN Y MEJORA

### Próximos pasos (NO implementados aún):

- [ ] Backtesting histórico
- [ ] Tracking de accuracy real
- [ ] Ajuste dinámico de pesos
- [ ] Incorporar más indicadores (MACD, Bollinger, EMA)
- [ ] Machine Learning (cuando haya datos suficientes)

---

## 📚 REFERENCIAS TÉCNICAS

- **RSI (Relative Strength Index)**: J. Welles Wilder, 1978
- **Technical Analysis**: John J. Murphy, "Technical Analysis of Financial Markets"
- **Momentum Indicators**: Martin Pring, "Technical Analysis Explained"

---

## 🤝 INTEGRACIÓN CON EL SISTEMA

```
┌─────────────────────────────────────────────────────────┐
│                    KRAKEN BOT ENGINE                     │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  1. Fetch OHLCV (Kraken API)                            │
│  2. Calculate RSI                                        │
│  3. Generate Prediction ← NUEVA CAPA                    │
│  4. Save State (JSON)                                    │
│  5. Detect Alerts                                        │
│                                                          │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│                   data/bot_state.json                    │
├─────────────────────────────────────────────────────────┤
│  {                                                       │
│    "BTC/USD": {                                          │
│      "last_price": 87080.00,                             │
│      "rsi_value": 45.32,                                 │
│      "rsi_state": "NEUTRAL",                             │
│      "prediction": {                    ← NUEVO          │
│        "direction": "UP",                                │
│        "confidence": 0.63,                               │
│        ...                                               │
│      }                                                   │
│    }                                                     │
│  }                                                       │
└─────────────────────────────────────────────────────────┘
                           ↓
┌─────────────────────────────────────────────────────────┐
│              FASTAPI OBSERVER (Read-Only)                │
├─────────────────────────────────────────────────────────┤
│  GET /api/status          → Incluye predicción          │
│  GET /api/predictions     → Solo predicciones  ← NUEVO  │
│  GET /api/predictions/{symbol}                ← NUEVO   │
└─────────────────────────────────────────────────────────┘
```

---

## 💡 CONSEJOS DE USO

1. **No operar solo con predicciones**: Úsalas como confirmación adicional
2. **Verificar calidad**: Priorizar predicciones HIGH y MEDIUM
3. **Leer las razones**: Entender el "por qué" de la predicción
4. **Considerar contexto**: Timeframe, volatilidad, eventos externos
5. **Combinar con otras herramientas**: Stop-loss, gestión de riesgo, análisis fundamental

---

## 📞 SOPORTE

Para preguntas o mejoras, revisar:

- [STRUCTURE.md](../backend/STRUCTURE.md) - Arquitectura del sistema
- [SUMMARY.md](../backend/SUMMARY.md) - Resumen del backend
- Código fuente: `predictive/predictor.py`

---

**🚨 DISCLAIMER**: Este sistema es EDUCATIVO y de OBSERVACIÓN. NO constituye asesoría financiera. El trading conlleva riesgos significativos de pérdida. Úsalo bajo tu propia responsabilidad.
