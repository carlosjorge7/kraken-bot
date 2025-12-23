"""
RSI - Relative Strength Index (Índice de Fuerza Relativa)

Implementación del indicador RSI para análisis técnico.
Este módulo está listo para usar pero NO se utiliza aún en el sistema.
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.DataFrame:
    """
    Calcula el RSI (Relative Strength Index) para una serie de precios.
    
    El RSI es un oscilador de momentum que mide la velocidad y el cambio
    de los movimientos de precio. Oscila entre 0 y 100.
    
    Interpretación tradicional:
    - RSI > 70: Condición de sobrecompra
    - RSI < 30: Condición de sobreventa
    - RSI = 50: Punto neutral
    
    Args:
        df: DataFrame con datos de precios
        period: Periodo para el cálculo del RSI (default: 14)
        column: Nombre de la columna con los precios (default: 'close')
    
    Returns:
        pd.DataFrame: DataFrame original con columna 'rsi' añadida
    
    Example:
        >>> df = pd.DataFrame({'close': [100, 102, 101, 103, 105, 104]})
        >>> df = calculate_rsi(df, period=5)
        >>> print(df['rsi'])
    """
    # Validar que existe la columna de precios
    if column not in df.columns:
        raise ValueError(f"La columna '{column}' no existe en el DataFrame")
    
    # Validar que hay suficientes datos
    if len(df) < period + 1:
        raise ValueError(
            f"Se necesitan al menos {period + 1} datos para calcular RSI "
            f"con periodo={period}. DataFrame tiene {len(df)} filas."
        )
    
    # Crear una copia del DataFrame para no modificar el original
    result_df = df.copy()
    
    # Calcular cambios de precio
    delta = result_df[column].diff()
    
    # Separar ganancias y pérdidas
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    
    # Calcular promedios móviles exponenciales
    # Nota: Usamos el método smoothed moving average (Wilder)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    
    # Calcular RS (Relative Strength)
    rs = avg_gain / avg_loss
    
    # Calcular RSI
    rsi = 100 - (100 / (1 + rs))
    
    # Añadir RSI al DataFrame
    result_df['rsi'] = rsi
    
    return result_df


def get_rsi_signal(rsi_value: float, overbought: float = 70, oversold: float = 30) -> str:
    """
    Interpreta el valor del RSI y devuelve una señal.
    
    Args:
        rsi_value: Valor actual del RSI
        overbought: Nivel de sobrecompra (default: 70)
        oversold: Nivel de sobreventa (default: 30)
    
    Returns:
        str: Señal interpretada ('OVERBOUGHT', 'OVERSOLD', 'NEUTRAL')
    """
    if pd.isna(rsi_value):
        return 'UNKNOWN'
    
    if rsi_value >= overbought:
        return 'OVERBOUGHT'
    elif rsi_value <= oversold:
        return 'OVERSOLD'
    else:
        return 'NEUTRAL'


def analyze_rsi(df: pd.DataFrame, period: int = 14) -> dict:
    """
    Calcula el RSI y proporciona un análisis completo.
    
    Args:
        df: DataFrame con datos OHLCV
        period: Periodo para el cálculo del RSI
    
    Returns:
        dict: Análisis completo del RSI con métricas y señales
    """
    # Calcular RSI
    df_with_rsi = calculate_rsi(df, period=period)
    
    # Obtener último valor de RSI
    latest_rsi = df_with_rsi['rsi'].iloc[-1]
    
    # Obtener señal
    signal = get_rsi_signal(latest_rsi)
    
    # Calcular estadísticas
    rsi_values = df_with_rsi['rsi'].dropna()
    
    analysis = {
        'current_rsi': latest_rsi,
        'signal': signal,
        'period': period,
        'stats': {
            'mean': rsi_values.mean(),
            'min': rsi_values.min(),
            'max': rsi_values.max(),
            'std': rsi_values.std(),
        }
    }
    
    return analysis
