"""
Configuration - Backend Settings
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Configuración del backend FastAPI"""
    
    # API Settings
    API_TITLE: str = "Kraken Bot Observer API"
    API_VERSION: str = "1.0.0"
    API_DESCRIPTION: str = "API de observación para el sistema Kraken Bot"
    
    # CORS
    CORS_ORIGINS: List[str] = ["*"]  # En producción, especificar dominios
    
    # Database
    DATABASE_PATH: str = "data/ohlcv.db"
    
    # State File (para compartir estado entre bot y API)
    STATE_FILE: str = "data/bot_state.json"
    ALERTS_FILE: str = "data/alerts.json"
    
    # WebSocket
    WS_HEARTBEAT_INTERVAL: int = 30  # segundos
    
    # Limits
    MAX_ALERTS_HISTORY: int = 100
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
