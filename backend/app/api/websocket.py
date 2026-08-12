"""Tiered WebSocket connection manager supporting public and authenticated admin streams."""

import json
import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from app.api.auth import verify_admin_token

logger = logging.getLogger(__name__)
router = APIRouter()


class TieredConnectionManager:
    """Manages separate public and admin WebSocket client connections."""

    def __init__(self):
        self.public_connections: List[WebSocket] = []
        self.admin_connections: List[WebSocket] = []

    async def connect_public(self, websocket: WebSocket):
        """Accept public WebSocket connection."""
        await websocket.accept()
        self.public_connections.append(websocket)
        logger.info(f"Public WS client connected. Total public clients: {len(self.public_connections)}")

    async def connect_admin(self, websocket: WebSocket):
        """Accept authenticated admin WebSocket connection."""
        await websocket.accept()
        self.admin_connections.append(websocket)
        logger.info(f"Admin WS client connected. Total admin clients: {len(self.admin_connections)}")

    def disconnect_public(self, websocket: WebSocket):
        """Remove disconnected public WebSocket client."""
        if websocket in self.public_connections:
            self.public_connections.remove(websocket)
            logger.info(f"Public WS client disconnected. Remaining: {len(self.public_connections)}")

    def disconnect_admin(self, websocket: WebSocket):
        """Remove disconnected admin WebSocket client."""
        if websocket in self.admin_connections:
            self.admin_connections.remove(websocket)
            logger.info(f"Admin WS client disconnected. Remaining: {len(self.admin_connections)}")

    async def _send_to_list(self, connections: List[WebSocket], message: Dict[str, Any], disconnect_func):
        if not connections:
            return
        payload = json.dumps(message)
        disconnected = []
        for conn in connections:
            try:
                await conn.send_text(payload)
            except Exception as e:
                logger.error(f"Error broadcasting WS message: {e}")
                disconnected.append(conn)

        for conn in disconnected:
            disconnect_func(conn)

    async def broadcast_public(self, message: Dict[str, Any]):
        """Broadcast event to public clients."""
        await self._send_to_list(self.public_connections, message, self.disconnect_public)

    async def broadcast_admin(self, message: Dict[str, Any]):
        """Broadcast event to authenticated admin clients."""
        await self._send_to_list(self.admin_connections, message, self.disconnect_admin)

    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast event to ALL connected clients (public & admin)."""
        await self.broadcast_public(message)
        await self.broadcast_admin(message)


ws_manager = TieredConnectionManager()


@router.websocket("/ws/public")
@router.websocket("/ws")
async def public_websocket_endpoint(websocket: WebSocket):
    """Public WebSocket stream for environment and anonymous gym stats."""
    await ws_manager.connect_public(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect_public(websocket)
    except Exception as e:
        logger.error(f"Public WebSocket error: {e}")
        ws_manager.disconnect_public(websocket)


@router.websocket("/ws/admin")
async def admin_websocket_endpoint(websocket: WebSocket, token: Optional[str] = None):
    """Authenticated Admin WebSocket stream for real-time check-in logs and locker card details."""
    if not token or not verify_admin_token(token):
        logger.warning("Rejected unauthenticated WebSocket attempt on /ws/admin")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized Token")
        return

    await ws_manager.connect_admin(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        ws_manager.disconnect_admin(websocket)
    except Exception as e:
        logger.error(f"Admin WebSocket error: {e}")
        ws_manager.disconnect_admin(websocket)
