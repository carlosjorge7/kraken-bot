"""
FastAPI Main Application

Backend de observación para Kraken Bot.

Este backend NO ejecuta lógica de trading.
SOLO expone el estado del sistema para consumo externo.
"""

from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging
import threading
import sys
import yaml
from pathlib import Path

from backend.app.config import settings
from backend.app.api.routes import router as api_router
from backend.app.api.websocket import websocket_handler


# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Variable global para el thread del bot
bot_thread = None
bot_engine = None


def run_bot():
    """Ejecuta el bot en modo continuo en un thread separado."""
    global bot_engine
    
    try:
        # Agregar el directorio raíz al path para imports
        root_dir = Path(__file__).parent.parent.parent
        if str(root_dir) not in sys.path:
            sys.path.insert(0, str(root_dir))
        
        # Importar después de ajustar el path
        from core.engine import Engine
        
        # Cargar configuración
        config_path = root_dir / 'config' / 'settings.yaml'
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        
        # Inicializar y ejecutar el engine
        bot_engine = Engine(config)
        logger.info("Motor del bot inicializado, comenzando ejecución continua...")
        bot_engine.run_continuous(setup_signals=False)  # No configurar signals en thread secundario
        
    except Exception as e:
        logger.error(f"Error ejecutando el bot: {e}", exc_info=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events"""
    global bot_thread, bot_engine
    
    # Startup
    logger.info("=" * 70)
    logger.info("🚀 KRAKEN BOT OBSERVER API - INICIANDO")
    logger.info("=" * 70)
    logger.info(f"📚 Documentación: http://localhost:8001/docs")
    logger.info(f"🔌 WebSocket: ws://localhost:8001/ws/alerts")
    logger.info("=" * 70)
    
    # Iniciar bot en thread separado
    logger.info("🤖 Iniciando Kraken Bot en segundo plano...")
    bot_thread = threading.Thread(target=run_bot, daemon=True)
    bot_thread.start()
    logger.info("✓ Bot iniciado correctamente")
    logger.info("=" * 70)
    
    yield
    
    # Shutdown
    logger.info("=" * 70)
    logger.info("🛑 KRAKEN BOT OBSERVER API - DETENIENDO")
    logger.info("=" * 70)
    
    # Detener bot
    if bot_engine:
        logger.info("Deteniendo bot...")
        bot_engine.stop()
    
    logger.info("Sistema detenido completamente")
    logger.info("=" * 70)


# Crear aplicación
app = FastAPI(
    title=settings.API_TITLE,
    version=settings.API_VERSION,
    description=settings.API_DESCRIPTION,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan
)


# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Registrar rutas REST
app.include_router(api_router, prefix="/api")


# WebSocket endpoint
@app.websocket("/ws/alerts")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket para alertas en tiempo real.
    
    Conexión:
        ws://localhost:8001/ws/alerts
    
    Mensajes enviados:
        - type: "connected" - Confirmación de conexión
        - type: "alert" - Nueva alerta detectada
        - type: "heartbeat" - Keepalive
    """
    await websocket_handler(websocket)


# Root endpoint
@app.get("/")
async def root():
    """
    Endpoint raíz con información de la API.
    """
    return {
        "name": settings.API_TITLE,
        "version": settings.API_VERSION,
        "description": "API de observación para Kraken Bot",
        "status": "running",
        "endpoints": {
            "health": "/api/health",
            "markets": "/api/markets",
            "status": "/api/status",
            "alerts": "/api/alerts",
            "websocket": "ws://localhost:8001/ws/alerts"
        },
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
