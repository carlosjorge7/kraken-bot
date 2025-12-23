"""
Módulo Fetcher - Obtención de Datos de Mercado

Este módulo contiene clases y funciones para obtener datos
de diferentes exchanges de criptomonedas.
"""

from .kraken_client import KrakenClient

__all__ = ['KrakenClient']
