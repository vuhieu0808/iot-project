"""REST API and WebSocket routes package."""

from app.api.websocket import ws_manager, router as ws_router
from app.api.routes_public import router as public_router
from app.api.routes_user import router as user_router
from app.api.routes_admin import router as admin_router
from app.api.routes_members import router as members_router
from app.api.routes_environment import router as environment_router
from app.api.routes_lockers import router as lockers_router
from app.api.routes_logs import router as logs_router

__all__ = [
    "ws_manager",
    "ws_router",
    "public_router",
    "user_router",
    "admin_router",
    "members_router",
    "environment_router",
    "lockers_router",
    "logs_router",
]

