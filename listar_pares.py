#!/usr/bin/env python3
"""
Listar Pares Disponibles en Kraken

Muestra todos los pares de trading disponibles en Kraken.
Útil para configurar el símbolo en settings.yaml

Uso:
    python listar_pares.py
    python listar_pares.py --filter BTC
"""

import sys
import argparse
import ccxt


def main():
    parser = argparse.ArgumentParser(description='Lista pares disponibles en Kraken')
    parser.add_argument('--filter', type=str, help='Filtrar por moneda (ej: BTC, ETH)')
    args = parser.parse_args()
    
    print("=" * 70)
    print("  PARES DISPONIBLES EN KRAKEN")
    print("=" * 70)
    print()
    print("Conectando con Kraken...")
    
    try:
        exchange = ccxt.kraken()
        markets = exchange.load_markets()
        pairs = list(markets.keys())
        
        # Filtrar si se especificó
        if args.filter:
            filter_upper = args.filter.upper()
            pairs = [p for p in pairs if filter_upper in p]
            print(f"Mostrando pares que contienen '{filter_upper}':")
        else:
            print(f"Total de pares disponibles: {len(pairs)}")
        
        print()
        
        # Mostrar pares
        for pair in sorted(pairs):
            print(f"  {pair}")
        
        print()
        print("=" * 70)
        print()
        print("Para usar un par, edita config/settings.yaml:")
        print("  exchange:")
        print("    symbol: \"BTC/USD\"  # Cambia esto por el par deseado")
        print()
        
        return 0
        
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
