"""GymTag Backend Main Application Entrypoint."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

from app.config import settings
from app.repositories.firebase_repo import FirebaseRepository
from app.services.notification_service import NotificationService
from app.services.access_service import AccessService
from app.services.locker_service import LockerService
from app.services.environment_service import EnvironmentService
from app.services.occupancy_service import OccupancyService
from app.services.repscounter_service import RepsCounterService
from app.mqtt.client import MQTTClient
from app.mqtt.handlers import MQTTMessageHandler
from app.api import (
    public_router,
    user_router,
    admin_router,
    members_router,
    environment_router,
    lockers_router,
    logs_router,
    ws_router,
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
        proxy=settings.TELEGRAM_PROXY,
    )

    access_service = AccessService(repository=repo)
    locker_service = LockerService(repository=repo)
    environment_service = EnvironmentService(
        repository=repo,
        notification_service=notification_service,
        temp_threshold=settings.TEMP_THRESHOLD,
        humidity_threshold=settings.HUMIDITY_THRESHOLD,
        alert_reminder_interval=settings.ALERT_REMINDER_INTERVAL_MINUTES * 60.0,
    )


    # Load saved thresholds from database if available (overrides .env defaults)
    try:
        saved_thresholds = await repo.get_environment_thresholds()
        if saved_thresholds:
            temp_val = float(saved_thresholds.get("temp_threshold", settings.TEMP_THRESHOLD))
            hum_val = float(saved_thresholds.get("humidity_threshold", settings.HUMIDITY_THRESHOLD))
            environment_service.update_thresholds(temp_threshold=temp_val, humidity_threshold=hum_val)
            logger.info(f"Loaded persistent environment thresholds: temp={temp_val}°C, humidity={hum_val}%")
    except Exception as e:
        logger.warning(f"Could not load persistent environment thresholds: {e}")

    occupancy_service = OccupancyService(repository=repo)

    repscounter_service = RepsCounterService(repository=repo)

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
        occupancy_service=occupancy_service,
        repscounter_service=repscounter_service,
        publish_func=mqtt_client.publish,
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
    description="Python Backend for RFID Gym Management & Monitoring System with Tiered Access Control",
    version="2.0.0",
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
app.include_router(public_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(members_router)
app.include_router(environment_router)
app.include_router(lockers_router)
app.include_router(logs_router)
app.include_router(ws_router)

# Serve Frontend static files seamlessly
frontend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "frontend"))
if os.path.exists(frontend_dir):
    shared_dir = os.path.join(frontend_dir, "shared")
    public_dir = os.path.join(frontend_dir, "public")
    user_dir = os.path.join(frontend_dir, "user")
    admin_dir = os.path.join(frontend_dir, "admin")

    os.makedirs(shared_dir, exist_ok=True)
    os.makedirs(public_dir, exist_ok=True)
    os.makedirs(user_dir, exist_ok=True)
    os.makedirs(admin_dir, exist_ok=True)

    app.mount("/shared", StaticFiles(directory=shared_dir), name="shared")
    app.mount("/public", StaticFiles(directory=public_dir, html=True), name="public")
    app.mount("/user", StaticFiles(directory=user_dir, html=True), name="user")
    app.mount("/admin", StaticFiles(directory=admin_dir, html=True), name="admin")
    app.mount("/frontend", StaticFiles(directory=frontend_dir, html=True), name="frontend")

static_dir = os.path.join(os.path.dirname(__file__), "static")
os.makedirs(static_dir, exist_ok=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.get("/", include_in_schema=False)
async def serve_root():
    """Redirect root '/' to Public Gym Dashboard at '/public/'."""
    return RedirectResponse(url="/public/")


@app.get("/public", include_in_schema=False)
async def redirect_public():
    """Redirect '/public' to '/public/'."""
    return RedirectResponse(url="/public/")


@app.get("/user", include_in_schema=False)
async def redirect_user():
    """Redirect '/user' to '/user/'."""
    return RedirectResponse(url="/user/")


@app.get("/admin", include_in_schema=False)
async def redirect_admin():
    """Redirect '/admin' to '/admin/'."""
    return RedirectResponse(url="/admin/")
