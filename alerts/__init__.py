"""
Módulo Alerts - Sistema de Alertas

Este módulo contiene clases para enviar alertas a diferentes canales
(Telegram, email, etc.) para uso futuro.
"""

from .telegram import TelegramAlert

__all__ = ['TelegramAlert']
