"""
Pydantic Schemas - Response Models
"""

from pydantic import BaseModel, Field
from typing import Optional, List
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
