"""GymTag Backend Main Application Entrypoint."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from app.config import settings
from app.repositories.firebase_repo import FirebaseRepository
from app.services.notification_service import NotificationService
from app.services.access_service import AccessService
from app.services.locker_service import LockerService
from app.services.environment_service import EnvironmentService
from app.services.occupancy_service import OccupancyService
from app.mqtt.client import MQTTClient
from app.mqtt.handlers import MQTTMessageHandler
from app.api import (
    members_router,
    lockers_router,
    environment_router,
    logs_router,
    ws_router,
    ConnectionManager,
    ws_manager,
)

# Configure standard Python logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle events."""
    logger.info("Initializing GymTag Backend Application...")

    # 1. Initialize Firebase Repository
    if not os.path.exists(settings.FIREBASE_CREDENTIALS_PATH):
        raise FileNotFoundError(f"Firebase credentials file not found at: {settings.FIREBASE_CREDENTIALS_PATH}")
    if not settings.FIREBASE_DATABASE_URL:
        raise ValueError("FIREBASE_DATABASE_URL environment variable is missing.")

    repo = FirebaseRepository(
        credentials_path=settings.FIREBASE_CREDENTIALS_PATH,
        database_url=settings.FIREBASE_DATABASE_URL,
        default_locker_count=settings.LOCKER_COUNT,
    )
    await repo.initialize()
    logger.info("Using Firebase Realtime Database repository.")

    # 2. Instantiate Services
    notification_service = NotificationService(
        bot_token=settings.TELEGRAM_BOT_TOKEN,
        chat_id=settings.TELEGRAM_CHAT_ID,
    )

    access_service = AccessService(repository=repo)
    locker_service = LockerService(repository=repo)
    environment_service = EnvironmentService(
        repository=repo,
        notification_service=notification_service,
        temp_threshold=settings.TEMP_THRESHOLD,
        humidity_threshold=settings.HUMIDITY_THRESHOLD,
    )
    occupancy_service = OccupancyService(repository=repo)

    # Attach services to app state for API route access
    app.state.repository = repo
    app.state.access_service = access_service
    app.state.locker_service = locker_service
    app.state.environment_service = environment_service
    app.state.occupancy_service = occupancy_service
    app.state.notification_service = notification_service

    # 3. Setup MQTT Client & Handler
    mqtt_client = MQTTClient(
        broker=settings.MQTT_BROKER,
        port=settings.MQTT_PORT,
        username=settings.MQTT_USERNAME,
        password=settings.MQTT_PASSWORD,
        client_id=settings.MQTT_CLIENT_ID,
    )

    mqtt_handler = MQTTMessageHandler(
        access_service=access_service,
        locker_service=locker_service,
        environment_service=environment_service,
        publish_func=mqtt_client.publish,
        broadcast_ws_func=ws_manager.broadcast,
    )

    loop = asyncio.get_running_loop()
    mqtt_client.set_async_handler(mqtt_handler.handle_message, loop)
    mqtt_client.connect()

    app.state.mqtt_client = mqtt_client

    logger.info("GymTag Backend fully initialized and running.")
    yield

    # Shutdown logic
    logger.info("Shutting down GymTag Backend Application...")
    mqtt_client.disconnect()


app = FastAPI(
    title="GymTag Backend API",
    description="Python Backend for RFID Gym Management & Monitoring System",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for dashboard access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register REST and WebSocket Routers
app.include_router(members_router)
app.include_router(lockers_router)
app.include_router(environment_router)
app.include_router(logs_router)
app.include_router(ws_router)

# Serve Frontend static files seamlessly
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    shared_dir = os.path.join(frontend_dir, "shared")
    user_dir = os.path.join(frontend_dir, "user")
    admin_dir = os.path.join(frontend_dir, "admin")

    if os.path.exists(shared_dir):
        app.mount("/shared", StaticFiles(directory=shared_dir), name="shared")
    if os.path.exists(user_dir):
        app.mount("/user", StaticFiles(directory=user_dir, html=True), name="user")
    if os.path.exists(admin_dir):
        app.mount("/admin", StaticFiles(directory=admin_dir, html=True), name="admin")
    
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

static_dir = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_dir):
    os.makedirs(static_dir, exist_ok=True)

app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def serve_root():
    """Redirect root '/' to User Dashboard at '/user/'."""
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/user/")

