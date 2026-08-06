from fastapi import WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio

class ChannelManager:
    def __init__(self, name: str):
        self.name = name
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: Dict[str, Any]):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message))
            except Exception:
                disconnected.append(connection)
        for conn in disconnected:
            self.disconnect(conn)

manager = ChannelManager("live")
signals_manager = ChannelManager("signals")
logs_manager = ChannelManager("logs")
heartbeat_manager = ChannelManager("heartbeat")
