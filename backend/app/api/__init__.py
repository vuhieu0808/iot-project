"""REST API and WebSocket routes package."""

from app.api.websocket import ws_manager, router as ws_router
from app.api.routes_public import router as public_router
from app.api.routes_user import router as user_router
from app.api.routes_admin import router as admin_router

__all__ = [
    "ws_manager",
    "ws_router",
    "public_router",
    "user_router",
    "admin_router",
]
