"""Configuration module for reading environment variables."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables or .env file."""

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    MQTT_BROKER: str = "test.mosquitto.org"
    MQTT_PORT: int = 1883
    MQTT_USERNAME: Optional[str] = None
    MQTT_PASSWORD: Optional[str] = None
    MQTT_CLIENT_ID: str = "gymtag_backend_service"

    TEMP_THRESHOLD: float = 32.0
    HUMIDITY_THRESHOLD: float = 80.0

    TELEGRAM_BOT_TOKEN: Optional[str] = None
    TELEGRAM_CHAT_ID: Optional[str] = None

    FIREBASE_CREDENTIALS_PATH: str = "firebase-admin-sdk.json"
    FIREBASE_DATABASE_URL: Optional[str] = None

    LOCKER_COUNT: int = 10

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
