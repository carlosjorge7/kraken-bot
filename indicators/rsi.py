"""
RSI - Relative Strength Index (Índice de Fuerza Relativa)

Implementación del indicador RSI para análisis técnico.
"""

import pandas as pd
import numpy as np
from typing import Optional


def calculate_rsi(df: pd.DataFrame, period: int = 14, column: str = 'close') -> pd.Series:
    """
    Calcula el RSI (Relative Strength Index) usando el método de Wilder.

    El RSI mide la velocidad y magnitud de los cambios de precio,
    oscilando entre 0 y 100.

    Fórmula:
        RSI = 100 - (100 / (1 + RS))
        RS = Promedio de ganancias / Promedio de pérdidas

    Args:
        df: DataFrame con datos de precios
        period: Periodo para el cálculo (default: 14)
        column: Columna a usar para el cálculo (default: 'close')

    Returns:
        pd.Series: Serie con valores RSI (NaN donde no hay datos suficientes)

    Raises:
        ValueError: Si la columna no existe o no hay suficientes datos
    """
    if column not in df.columns:
        raise ValueError(f"Columna '{column}' no encontrada en DataFrame")

    if len(df) < period + 1:
        raise ValueError(
            f"Se requieren al menos {period + 1} datos. "
            f"DataFrame tiene {len(df)} filas"
        )

    # Calcular cambios de precio
    delta = df[column].diff()

    # Separar ganancias y pérdidas
    gain = delta.clip(lower=0).values
    loss = (-delta.clip(upper=0)).values

    # Usar arrays numpy para evitar problemas de asignación con pandas 2.x
    avg_gain = np.full(len(df), np.nan)
    avg_loss = np.full(len(df), np.nan)

    # Primera media: SMA de los primeros `period` valores
    avg_gain[period - 1] = np.mean(gain[1:period + 1])
    avg_loss[period - 1] = np.mean(loss[1:period + 1])

    # Medias subsecuentes: Smoothed (método de Wilder)
    for i in range(period, len(df)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gain[i]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + loss[i]) / period

    # Calcular RS y RSI evitando división por cero
    with np.errstate(divide='ignore', invalid='ignore'):
        rs = np.where(avg_loss == 0, np.inf, avg_gain / avg_loss)
    rsi_values = 100 - (100 / (1 + rs))

    return pd.Series(rsi_values, index=df.index)


def get_rsi_signal(rsi_value: float, overbought: float = 70, oversold: float = 30) -> str:
    """
    Interpreta el valor del RSI.
    
    Args:
        rsi_value: Valor del RSI
        overbought: Umbral de sobrecompra (default: 70)
        oversold: Umbral de sobreventa (default: 30)
    
    Returns:
        str: 'OVERBOUGHT', 'OVERSOLD', 'NEUTRAL', o 'UNKNOWN'
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
    Calcula RSI y devuelve análisis estadístico.
    
    Args:
        df: DataFrame con datos OHLCV
        period: Periodo para el cálculo
    
    Returns:
        dict: Diccionario con RSI actual, señal y estadísticas
    """
    rsi = calculate_rsi(df, period=period)
    latest_rsi = rsi.iloc[-1]
    signal = get_rsi_signal(latest_rsi)
    
    rsi_valid = rsi.dropna()
    
    return {
        'current_rsi': latest_rsi,
        'signal': signal,
        'period': period,
        'stats': {
            'mean': rsi_valid.mean(),
            'min': rsi_valid.min(),
            'max': rsi_valid.max(),
            'std': rsi_valid.std(),
        }
    }