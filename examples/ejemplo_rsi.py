#!/usr/bin/env python3
"""
Ejemplo de Uso - Cálculo de RSI

Este script muestra cómo usar el indicador RSI con datos de Kraken.
Se puede ejecutar independientemente de main.py.

Uso:
    python examples/ejemplo_rsi.py
"""

import sys
import os

# Añadir directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import yaml
from pathlib import Path
from fetcher import KrakenClient
from indicators import calculate_rsi
import pandas as pd

pd.set_option('display.max_rows', None)
pd.set_option('display.width', None)


def main():
    """Función principal del ejemplo."""
    
    print("=" * 70)
    print("  EJEMPLO: Cálculo de RSI con Datos de Kraken")
    print("=" * 70)
    print()
    
    # 1. Cargar configuración
    print("📋 Cargando configuración...")
    config_path = Path('config/settings.yaml')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    symbol = config['exchange']['symbol']
    timeframe = config['exchange']['timeframe']
    rsi_period = config['indicators']['rsi']['period']
    
    print(f"   • Par: {symbol}")
    print(f"   • Timeframe: {timeframe}")
    print(f"   • Periodo RSI: {rsi_period}")
    print()
    
    # 2. Obtener datos de Kraken
    print("📡 Conectando con Kraken...")
    client = KrakenClient()
    
    print(f"📊 Descargando datos OHLCV...")
    df = client.fetch_ohlcv(
        symbol=symbol,
        timeframe=timeframe,
        limit=100
    )
    
    print(f"✓ Se obtuvieron {len(df)} velas")
    print()
    
    # 3. Calcular RSI
    print("🔢 Calculando RSI...")
    df = calculate_rsi(df, period=rsi_period)
    
    # 4. Mostrar resultados
    print("=" * 70)
    print("ÚLTIMAS 10 VELAS CON RSI")
    print("=" * 70)
    
    # Seleccionar columnas relevantes
    display_df = df[['timestamp', 'close', 'rsi']].tail(10)
    
    # Formatear para mejor visualización
    display_df = display_df.copy()
    display_df['close'] = display_df['close'].apply(lambda x: f"${x:,.2f}")
    display_df['rsi'] = display_df['rsi'].apply(lambda x: f"{x:.2f}" if pd.notna(x) else "N/A")
    
    print(display_df.to_string(index=False))
    print()
    
    # 5. Análisis del RSI actual
    latest = df.iloc[-1]
    rsi_value = latest['rsi']
    
    overbought = config['indicators']['rsi']['overbought']
    oversold = config['indicators']['rsi']['oversold']
    
    print("=" * 70)
    print("ANÁLISIS RSI ACTUAL")
    print("=" * 70)
    print(f"Valor RSI:           {rsi_value:.2f}")
    print(f"Umbral sobrecompra:  {overbought}")
    print(f"Umbral sobreventa:   {oversold}")
    print()
    
    # Interpretación
    if rsi_value >= overbought:
        print("🔴 SEÑAL: SOBRECOMPRA")
        print("   El mercado podría estar sobrecomprado.")
        print("   Posible corrección a la baja.")
    elif rsi_value <= oversold:
        print("🟢 SEÑAL: SOBREVENTA")
        print("   El mercado podría estar sobrevendido.")
        print("   Posible rebote al alza.")
    else:
        print("⚪ SEÑAL: NEUTRAL")
        print("   El mercado está en zona neutral.")
        print("   No hay señales claras de sobrecompra/sobreventa.")
    
    print()
    print("=" * 70)
    print()
    
    # 6. Estadísticas adicionales
    print("ESTADÍSTICAS DEL RSI (últimas 100 velas)")
    print("-" * 70)
    rsi_stats = df['rsi'].describe()
    print(f"  Media:       {rsi_stats['mean']:.2f}")
    print(f"  Mínimo:      {rsi_stats['min']:.2f}")
    print(f"  Máximo:      {rsi_stats['max']:.2f}")
    print(f"  Desv. Std:   {rsi_stats['std']:.2f}")
    print()
    
    # Contar señales
    sobrecompra_count = (df['rsi'] >= overbought).sum()
    sobreventa_count = (df['rsi'] <= oversold).sum()
    
    print(f"  Velas en sobrecompra:  {sobrecompra_count}")
    print(f"  Velas en sobreventa:   {sobreventa_count}")
    print()
    
    print("✅ Ejemplo completado exitosamente")
    print()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠️ Ejemplo interrumpido por el usuario\n")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)
