"""
WebSocket Handler - Real-time Alerts

WebSocket endpoint para recibir alertas en tiempo real.
"""

import asyncio
import json
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime
from typing import Set
from pathlib import Path

from backend.app.models.schemas import WSAlertMessage, WSHeartbeat, Alert
from backend.app.config import settings
from backend.app.services.state_reader import state_reader


class ConnectionManager:
    """
    Gestor de conexiones WebSocket.
    
    Mantiene track de clientes conectados y envía mensajes.
    """
    
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.last_alert_id: int = -1
    
    async def connect(self, websocket: WebSocket):
        """Acepta una nueva conexión"""
        await websocket.accept()
        self.active_connections.add(websocket)
    
    def disconnect(self, websocket: WebSocket):
        """Remueve una conexión"""
        self.active_connections.discard(websocket)
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Envía un mensaje a un cliente específico"""
        try:
            await websocket.send_json(message)
        except:
            self.disconnect(websocket)
    
    async def broadcast(self, message: dict):
        """Envía un mensaje a todos los clientes conectados"""
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except:
                disconnected.add(connection)
        
        # Limpiar conexiones muertas
        for conn in disconnected:
            self.disconnect(conn)
    
    async def send_heartbeat(self):
        """Envía heartbeat a todos los clientes"""
        heartbeat = WSHeartbeat(
            timestamp=datetime.now().isoformat()
        )
        await self.broadcast(heartbeat.dict())
    
    async def check_new_alerts(self):
        """
        Verifica si hay nuevas alertas y las envía.
        
        Este método se ejecuta periódicamente en background.
        """
        alerts = state_reader.get_alerts(limit=1)
        
        if not alerts:
            return
        
        latest_alert = alerts[0]
        
        # Si es una alerta nueva, enviarla
        if latest_alert.id and latest_alert.id > self.last_alert_id:
            self.last_alert_id = latest_alert.id
            
            message = WSAlertMessage(
                alert=latest_alert,
                timestamp=datetime.now().isoformat()
            )
            
            await self.broadcast(message.dict())


# Singleton
manager = ConnectionManager()


async def websocket_handler(websocket: WebSocket):
    """
    Handler principal del WebSocket.
    
    Mantiene la conexión abierta y envía:
    - Heartbeats periódicos
    - Nuevas alertas cuando se detectan
    """
    await manager.connect(websocket)
    
    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "connected",
            "message": "Conectado al sistema de alertas",
            "timestamp": datetime.now().isoformat()
        })
        
        # Loop principal
        while True:
            # Esperar mensaje del cliente (o timeout)
            try:
                # Timeout de 5 segundos para verificar alertas
                data = await asyncio.wait_for(
                    websocket.receive_text(),
                    timeout=5.0
                )
                
                # Procesar mensaje del cliente si es necesario
                # Por ahora, solo lo ignoramos
                
            except asyncio.TimeoutError:
                # Timeout normal, verificar alertas
                await manager.check_new_alerts()
                
                # Enviar heartbeat cada N segundos
                # (implementación simplificada)
                await manager.send_heartbeat()
            
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        manager.disconnect(websocket)
        raise
