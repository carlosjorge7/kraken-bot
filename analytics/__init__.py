"""
Analytics Module - Evaluación y Análisis de Predicciones

Este módulo proporciona herramientas para:
- Backtesting de predicciones
- Métricas de accuracy
- Análisis de performance
"""

from .backtester import PredictionBacktester, BacktestResult

__all__ = ['PredictionBacktester', 'BacktestResult']
