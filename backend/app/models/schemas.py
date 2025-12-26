"""
Pydantic Schemas - Response Models
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from datetime import datetime
from enum import Enum


# ============================================================================
# ENUMS
# ============================================================================

class RSIState(str, Enum):
    """Estados posibles del RSI"""
    NEUTRAL = "NEUTRAL"
    OVERBOUGHT = "OVERBOUGHT"
    OVERSOLD = "OVERSOLD"


class PredictionDirection(str, Enum):
    """Direcciones posibles de predicción"""
    UP = "UP"
    DOWN = "DOWN"
    NEUTRAL = "NEUTRAL"


class PredictionHorizon(str, Enum):
    """Horizontes temporales para predicción"""
    NEXT_1_CANDLE = "next_1_candle"
    NEXT_3_CANDLES = "next_3_candles"
    NEXT_5_CANDLES = "next_5_candles"


class PredictionQuality(str, Enum):
    """Calidad de la predicción"""
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


# ============================================================================
# RESPONSE MODELS
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., example="ok")
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


class MarketInfo(BaseModel):
    """Información de un mercado monitoreado"""
    symbol: str = Field(..., example="BTC/USD")
    timeframe: str = Field(..., example="15m")


class MarketsResponse(BaseModel):
    """Lista de mercados monitoreados"""
    markets: List[MarketInfo]
    total: int


class MarketStatus(BaseModel):
    """Estado actual de un mercado"""
    symbol: str = Field(..., example="BTC/USD")
    timeframe: str = Field(..., example="15m")
    
    # Precio
    last_price: Optional[float] = Field(None, example=87894.10)
    
    # RSI
    rsi_value: Optional[float] = Field(None, example=45.32)
    rsi_state: Optional[RSIState] = Field(None, example="NEUTRAL")
    
    # Predicción (opcional)
    prediction: Optional[Prediction] = None
    
    # Timestamp
    last_update: Optional[str] = Field(None, example="2025-12-25T21:45:00")
    
    # Metadata
    data_available: bool = Field(..., example=True)


class StatusResponse(BaseModel):
    """Estado de todos los mercados"""
    markets: List[MarketStatus]
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


class Alert(BaseModel):
    """Modelo de una alerta"""
    id: Optional[int] = None
    symbol: str = Field(..., example="ETH/USD")
    rsi: float = Field(..., example=28.9)
    state: RSIState = Field(..., example="OVERSOLD")
    timestamp: str = Field(..., example="2025-12-25T21:45:00")
    message: Optional[str] = Field(None, example="⚠️ RSI en sobreventa")


class AlertsResponse(BaseModel):
    """Lista de alertas"""
    alerts: List[Alert]
    total: int
    last_update: Optional[str] = None


# ============================================================================
# WEBSOCKET MESSAGES
# ============================================================================

class WSMessage(BaseModel):
    """Mensaje genérico de WebSocket"""
    type: str = Field(..., example="alert")
    data: dict = Field(..., example={})
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


class WSAlertMessage(BaseModel):
    """Mensaje de alerta por WebSocket"""
    type: str = Field(default="alert", example="alert")
    alert: Alert
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


class WSHeartbeat(BaseModel):
    """Heartbeat para mantener conexión"""
    type: str = Field(default="heartbeat", example="heartbeat")
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


# ============================================================================
# PREDICTION MODELS
# ============================================================================

class TechnicalScores(BaseModel):
    """Scores técnicos individuales"""
    rsi_signal: float = Field(..., example=0.65)
    rsi_momentum: float = Field(..., example=0.42)
    price_momentum: float = Field(..., example=0.38)
    volume_trend: float = Field(..., example=0.51)


class Prediction(BaseModel):
    """Predicción de dirección del precio"""
    direction: PredictionDirection = Field(..., example="UP")
    confidence: float = Field(..., ge=0.0, le=1.0, example=0.63)
    horizon: PredictionHorizon = Field(..., example="next_3_candles")
    quality: PredictionQuality = Field(..., example="MEDIUM")
    reasons: List[str] = Field(
        ...,
        example=[
            "RSI en sobreventa (28.5) - probable rebote",
            "RSI con tendencia alcista",
            "Momentum de precio positivo"
        ]
    )
    technical_scores: Optional[TechnicalScores] = None
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


class MarketPrediction(BaseModel):
    """Predicción completa para un mercado"""
    symbol: str = Field(..., example="BTC/USD")
    timeframe: str = Field(..., example="15m")
    prediction: Prediction


class PredictionsResponse(BaseModel):
    """Respuesta con predicciones de múltiples mercados"""
    predictions: List[MarketPrediction]
    timestamp: str = Field(..., example="2025-12-25T22:00:00")


# ============================================================================
# BACKTESTING MODELS
# ============================================================================

class BacktestMetrics(BaseModel):
    """Métricas de backtesting"""
    total_predictions: int
    accuracy_1c: float
    accuracy_3c: float
    accuracy_5c: float
    accuracy_by_confidence: Dict[str, float]
    accuracy_by_quality: Dict[str, float]
    confusion_matrix: Dict[str, Dict[str, int]]
    timestamp: str


class BacktestSummary(BaseModel):
    """Resumen del estado del backtesting"""
    total_predictions: int
    verified: int
    pending_verification: int
    last_update: str



