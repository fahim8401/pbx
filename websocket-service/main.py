"""
WebSocket Service for Live Statistics
Provides real-time updates for active calls and system stats
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict, Set
import asyncio
import json
from datetime import datetime

app = FastAPI(title="HPLink PBX WebSocket Service")

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {
    "admin": set(),
    "tenant": {},
}


class ConnectionManager:
    """Manage WebSocket connections"""

    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        """Accept and store WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.discard(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        disconnected = set()
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected clients
        for conn in disconnected:
            self.active_connections.discard(conn)


manager = ConnectionManager()


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok", "service": "websocket"}


@app.websocket("/ws/admin")
async def websocket_admin(websocket: WebSocket):
    """WebSocket endpoint for admin portal"""
    await manager.connect(websocket)
    
    try:
        # Send initial connection message
        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        # Keep connection alive and handle incoming messages
        while True:
            data = await websocket.receive_text()
            # Echo back for now (in production, handle commands)
            await websocket.send_json({
                "type": "echo",
                "data": data,
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.websocket("/ws/tenant/{tenant_id}")
async def websocket_tenant(websocket: WebSocket, tenant_id: str):
    """WebSocket endpoint for tenant portal"""
    await manager.connect(websocket)
    
    try:
        await websocket.send_json({
            "type": "connected",
            "tenant_id": tenant_id,
            "timestamp": datetime.utcnow().isoformat(),
        })
        
        while True:
            data = await websocket.receive_text()
            await websocket.send_json({
                "type": "echo",
                "tenant_id": tenant_id,
                "data": data,
            })
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/broadcast/call-event")
async def broadcast_call_event(event: dict):
    """
    Receive call events from PBX core and broadcast to connected clients
    """
    message = {
        "type": "call_event",
        "event": event,
        "timestamp": datetime.utcnow().isoformat(),
    }
    
    await manager.broadcast(message)
    
    return {"status": "broadcasted"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
