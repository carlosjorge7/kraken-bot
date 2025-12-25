"""
API Routes - REST Endpoints

Endpoints de solo lectura para observar el estado del sistema.
"""

from fastapi import APIRouter, HTTPException
from datetime import datetime
from typing import Optional

from backend.app.models.schemas import (
    HealthResponse,
    MarketsResponse,
    StatusResponse,
    AlertsResponse
)
from backend.app.services.state_reader import state_reader


router = APIRouter()


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health Check",
    description="Verifica que la API esté funcionando"
)
async def health_check():
    """
    Health check simple.
    
    Returns:
        Estado del servicio
    """
    return HealthResponse(
        status="ok",
        timestamp=datetime.now().isoformat()
    )


@router.get(
    "/markets",
    response_model=MarketsResponse,
    summary="Lista de Mercados",
    description="Obtiene la lista de mercados monitoreados por el bot"
)
async def get_markets():
    """
    Obtiene los mercados monitoreados.
    
    Returns:
        Lista de mercados con símbolo y timeframe
    """
    markets = state_reader.get_markets()
    
    return MarketsResponse(
        markets=markets,
        total=len(markets)
    )


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Estado de Mercados",
    description="Obtiene el estado actual de todos los mercados (precio, RSI, etc.)"
)
async def get_status():
    """
    Obtiene el estado actual de todos los mercados.
    
    Incluye:
    - Último precio
    - RSI actual
    - Estado del RSI (NEUTRAL/OVERBOUGHT/OVERSOLD)
    - Timestamp de última actualización
    
    Returns:
        Estado de todos los mercados
    """
    statuses = state_reader.get_all_status()
    
    return StatusResponse(
        markets=statuses,
        timestamp=datetime.now().isoformat()
    )


@router.get(
    "/status/{symbol}",
    response_model=StatusResponse,
    summary="Estado de un Mercado",
    description="Obtiene el estado de un mercado específico"
)
async def get_market_status(symbol: str):
    """
    Obtiene el estado de un mercado específico.
    
    Args:
        symbol: Símbolo del mercado (ej: BTC/USD, BTC-USD, BTCUSD)
    
    Returns:
        Estado del mercado
    """
    # Normalizar símbolo
    symbol = symbol.replace('-', '/').replace('_', '/')
    
    status = state_reader.get_market_status(symbol)
    
    if not status:
        raise HTTPException(
            status_code=404,
            detail=f"Mercado '{symbol}' no encontrado"
        )
    
    return StatusResponse(
        markets=[status],
        timestamp=datetime.now().isoformat()
    )


@router.get(
    "/alerts",
    response_model=AlertsResponse,
    summary="Alertas Recientes",
    description="Obtiene las alertas más recientes detectadas por el bot"
)
async def get_alerts(limit: Optional[int] = 50):
    """
    Obtiene las alertas recientes.
    
    Args:
        limit: Número máximo de alertas a retornar (default: 50)
    
    Returns:
        Lista de alertas ordenadas por timestamp
    """
    alerts = state_reader.get_alerts(limit=limit)
    
    last_update = None
    if alerts:
        last_update = alerts[-1].timestamp
    
    return AlertsResponse(
        alerts=alerts,
        total=len(alerts),
        last_update=last_update
    )
