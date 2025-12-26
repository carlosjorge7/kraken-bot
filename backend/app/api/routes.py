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
    AlertsResponse,
    PredictionsResponse,
    BacktestMetrics,
    BacktestSummary
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
    "/status/{symbol:path}",
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


@router.get(
    "/predictions",
    response_model=PredictionsResponse,
    summary="Predicciones de Dirección",
    description="Obtiene predicciones probabilísticas de dirección para todos los mercados"
)
async def get_predictions():
    """
    Obtiene predicciones de dirección para todos los mercados.
    
    Las predicciones son probabilísticas (UP/DOWN/NEUTRAL) con nivel de confianza.
    NO predicen precio exacto, solo dirección probable.
    
    Returns:
        Predicciones para todos los mercados
    """
    predictions = state_reader.get_predictions()
    
    return PredictionsResponse(
        predictions=predictions,
        timestamp=datetime.now().isoformat()
    )


@router.get(
    "/predictions/{symbol:path}",
    response_model=PredictionsResponse,
    summary="Predicción de un Mercado",
    description="Obtiene la predicción de dirección para un mercado específico"
)
async def get_market_prediction(symbol: str):
    """
    Obtiene la predicción para un mercado específico.
    
    Args:
        symbol: Símbolo del mercado (ej: BTC/USD, BTC-USD, BTCUSD)
    
    Returns:
        Predicción del mercado
    """
    # Normalizar símbolo
    symbol = symbol.replace('-', '/').replace('_', '/')
    
    prediction = state_reader.get_market_prediction(symbol)
    
    if not prediction:
        raise HTTPException(
            status_code=404,
            detail=f"Predicción para '{symbol}' no encontrada"
        )
    
    return PredictionsResponse(
        predictions=[prediction],
        timestamp=datetime.now().isoformat()
    )


# ============================================================================
# BACKTESTING ENDPOINTS
# ============================================================================

@router.get(
    "/backtest/metrics",
    response_model=BacktestMetrics,
    summary="Métricas de Backtesting",
    description="Obtiene métricas históricas de precisión de predicciones"
)
async def get_backtest_metrics(
    symbol: Optional[str] = None,
    min_confidence: Optional[float] = None
):
    """
    Obtiene métricas detalladas del backtesting.
    
    Args:
        symbol: Filtrar por símbolo (ej: BTC/USD)
        min_confidence: Confianza mínima (0-1)
    
    Returns:
        Métricas de precisión por horizonte, confianza y calidad
    """
    try:
        metrics = state_reader.get_backtest_metrics(
            symbol=symbol,
            min_confidence=min_confidence
        )
        
        if not metrics:
            raise HTTPException(
                status_code=404,
                detail="No hay métricas de backtesting disponibles"
            )
        
        return metrics
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo métricas: {str(e)}"
        )


@router.get(
    "/backtest/summary",
    response_model=BacktestSummary,
    summary="Resumen de Backtesting",
    description="Obtiene un resumen del estado del backtesting"
)
async def get_backtest_summary():
    """
    Obtiene resumen del backtesting.
    
    Returns:
        Conteo de predicciones y última actualización
    """
    try:
        summary = state_reader.get_backtest_summary()
        
        if not summary:
            raise HTTPException(
                status_code=404,
                detail="No hay datos de backtesting disponibles"
            )
        
        return summary
    
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error obteniendo resumen: {str(e)}"
        )
