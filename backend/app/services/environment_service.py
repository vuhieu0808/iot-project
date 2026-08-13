"""Environment monitoring service for threshold evaluation and fan control."""

import logging
from typing import Any, Dict, Optional
from app.models.environment import EnvironmentReading
from app.repositories.base import BaseRepository
from app.services.notification_service import NotificationService

logger = logging.getLogger(__name__)


class EnvironmentService:
    """Processes temperature and humidity sensor readings and triggers fan control / Telegram alerts."""

    def __init__(
        self,
        repository: BaseRepository,
        notification_service: NotificationService,
        temp_threshold: float = 32.0,
        humidity_threshold: float = 80.0,
    ):
        self.repository = repository
        self.notification_service = notification_service
        self.temp_threshold = temp_threshold
        self.humidity_threshold = humidity_threshold
        self.fan_currently_on: bool = False

    async def process_reading(self, temperature: float, humidity: float) -> Dict[str, Any]:
        """Process incoming environment reading.

        Args:
            temperature: Temperature in Celsius.
            humidity: Humidity in percentage.

        Returns:
            Dict containing fan control output decision:
            {
                "fan_control_needed": bool,
                "fan_command": "on" | "off" | None,
                "reason": str,
                "reading": EnvironmentReading
            }
        """
        exceeds_threshold = (temperature > self.temp_threshold) or (humidity > self.humidity_threshold)
        fan_command: Optional[str] = None
        fan_control_needed = False
        reason = "Normal conditions"

        if exceeds_threshold:
            reason = f"Threshold exceeded! Temp: {temperature}C (limit {self.temp_threshold}C), Humidity: {humidity}% (limit {self.humidity_threshold}%)"
            if not self.fan_currently_on:
                self.fan_currently_on = True
                fan_command = "on"
                fan_control_needed = True

                # Send Telegram alert
                alert_msg = (
                    f"⚠️ <b>CANH BAO NHIET DO / DO AM PHONG GYM</b> ⚠️\n\n"
                    f"🌡️ Nhiet do: <b>{temperature:.1f}°C</b> (nguong: {self.temp_threshold}°C)\n"
                    f"💧 Do am: <b>{humidity:.1f}%</b> (nguong: {self.humidity_threshold}%)\n"
                    f"🌀 Dang gui lenh <b>BAT QUAT</b> tu dong sang ESP32."
                )
                await self.notification_service.send_alert(alert_msg, force=True)
                logger.warning(f"Environmental alert triggered: {reason}")
        else:
            if self.fan_currently_on:
                self.fan_currently_on = False
                fan_command = "off"
                fan_control_needed = True
                reason = "Conditions returned to normal. Turning off fan."

                # Send Telegram recovery notice
                recovery_msg = (
                    f"✅ <b>THONG BAO PHONG GYM</b> ✅\n\n"
                    f"Moi truong da tro lai binh thuong:\n"
                    f"🌡️ Nhiet do: {temperature:.1f}°C\n"
                    f"💧 Do am: {humidity:.1f}%\n"
                    f"🌀 Dang gui lenh <b>TAT QUAT</b>."
                )
                await self.notification_service.send_alert(recovery_msg, force=False)
                logger.info(f"Environment restored to normal: {reason}")

        # Save reading to repo
        reading = EnvironmentReading(
            temperature=temperature,
            humidity=humidity,
            fan_on=self.fan_currently_on,
        )
        await self.repository.add_environment_reading(reading)

        return {
            "fan_control_needed": fan_control_needed,
            "fan_command": fan_command,
            "reason": reason,
            "reading": reading,
        }

    async def set_fan_state(self, fan_on: bool, reason: str = "Manual control by Admin") -> EnvironmentReading:
        """Manually set fan state and record reading."""
        self.fan_currently_on = fan_on
        latest = await self.get_latest_reading()
        temp = latest.temperature if latest else 25.0
        humidity = latest.humidity if latest else 50.0

        reading = EnvironmentReading(
            temperature=temp,
            humidity=humidity,
            fan_on=self.fan_currently_on,
        )
        await self.repository.add_environment_reading(reading)
        return reading

    async def get_latest_reading(self) -> Optional[EnvironmentReading]:
        """Fetch latest environment reading."""
        return await self.repository.get_latest_reading()

    async def get_history(self, limit: int = 50):
        """Fetch historical readings."""
        return await self.repository.get_environment_readings(limit=limit)

