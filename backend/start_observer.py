#!/usr/bin/env python3
"""
Script de inicio para el Backend Observer API
"""

import sys
import os

# Asegurar que el directorio raíz esté en el path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 70)
    print("🚀 INICIANDO KRAKEN BOT OBSERVER API")
    print("=" * 70)
    print()
    print("📚 Documentación Swagger: http://localhost:8001/docs")
    print("📖 Documentación ReDoc:   http://localhost:8001/redoc")
    print("🔌 WebSocket Alerts:      ws://localhost:8001/ws/alerts")
    print()
    print("Presiona CTRL+C para detener el servidor")
    print("=" * 70)
    print()
    
    uvicorn.run(
        "backend.app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
        log_level="info"
    )
