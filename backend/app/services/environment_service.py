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
        temp_hysteresis: float = 1.0,
        humidity_hysteresis: float = 3.0,
        alert_reminder_interval: float = 900.0,
    ):
        self.repository = repository
        self.notification_service = notification_service
        self.temp_threshold = temp_threshold
        self.humidity_threshold = humidity_threshold
        self.temp_hysteresis = temp_hysteresis
        self.humidity_hysteresis = humidity_hysteresis
        self.fan_currently_on: bool = False
        self.manual_mode: bool = False
        self.manual_fan_state: Optional[bool] = None
        self.last_alert_time: float = 0.0
        self.alert_reminder_interval: float = alert_reminder_interval  # Configurable reminder interval in seconds


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
                "reading": EnvironmentReading,
                "manual_mode": bool
            }
        """
        import time
        from datetime import datetime

        now_iso = datetime.now().isoformat()
        now_time = time.time()
        now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")

        # 1. Sanity check: filter out corrupted sensor readings
        if not (-20.0 <= temperature <= 80.0) or not (0.0 <= humidity <= 100.0):
            logger.warning(
                f"Outlier or corrupted sensor reading ignored: Temp={temperature}°C, Humidity={humidity}%"
            )
            latest = await self.get_latest_reading()
            fallback = latest or EnvironmentReading(
                temperature=temperature,
                humidity=humidity,
                fan_on=self.fan_currently_on,
                timestamp=now_iso,
            )
            return {
                "fan_control_needed": False,
                "fan_command": None,
                "reason": f"Corrupted reading ignored: {temperature}°C, {humidity}%",
                "reading": fallback,
                "manual_mode": self.manual_mode,
            }

        # 2. Check if Admin Manual Mode is active (Admin Manual has highest priority)
        if self.manual_mode:
            reason = f"Chế độ điều khiển Thủ công (Manual) bởi Admin đang kích hoạt (Quạt: {'BẬT' if self.fan_currently_on else 'TẮT'}). Không tự động đổi trạng thái quạt."
            
            # Still send Telegram alert to notify admin if dangerous threshold is breached during manual mode
            exceeds_threshold = (temperature > self.temp_threshold) or (humidity > self.humidity_threshold)
            if exceeds_threshold:
                if (now_time - self.last_alert_time) >= self.alert_reminder_interval or self.last_alert_time == 0:
                    self.last_alert_time = now_time
                    alert_msg = (
                        f"🚨 <b>CẢNH BÁO MÔI TRƯỜNG PHÒNG GYM</b> 🚨\n\n"
                        f"🕒 <b>Thời gian:</b> <code>{now_str}</code>\n"
                        f"🌡️ <b>Nhiệt độ:</b> <b>{temperature:.1f}°C</b> (Ngưỡng: {self.temp_threshold:.1f}°C)\n"
                        f"💧 <b>Độ ẩm:</b> <b>{humidity:.1f}%</b> (Ngưỡng: {self.humidity_threshold:.1f}%)\n"
                        f"⚠️ <b>LƯU Ý:</b> Quạt đang ở chế độ <b>THỦ CÔNG ({'BẬT' if self.fan_currently_on else 'TẮT'})</b> do Admin ra lệnh."
                    )
                    await self.notification_service.send_alert(alert_msg, force=True)

            reading = EnvironmentReading(
                temperature=temperature,
                humidity=humidity,
                fan_on=self.fan_currently_on,
                timestamp=now_iso,
            )
            saved_reading = await self.repository.add_environment_reading(reading)

            return {
                "fan_control_needed": False,
                "fan_command": None,
                "reason": reason,
                "reading": saved_reading,
                "manual_mode": True,
            }

        # 3. Threshold evaluation with Hysteresis (Auto mode)
        exceeds_threshold = (temperature > self.temp_threshold) or (humidity > self.humidity_threshold)
        
        # Recovery condition requires falling below (Threshold - Hysteresis) to avoid chattering
        is_fully_recovered = (
            temperature <= (self.temp_threshold - self.temp_hysteresis)
            and humidity <= (self.humidity_threshold - self.humidity_hysteresis)
        )

        fan_command: Optional[str] = None
        fan_control_needed = False
        reason = "Normal conditions"

        if exceeds_threshold:
            reason = (
                f"Vượt ngưỡng cảnh báo! Nhiệt độ: {temperature:.1f}°C (ngưỡng: {self.temp_threshold:.1f}°C), "
                f"Độ ẩm: {humidity:.1f}% (ngưỡng: {self.humidity_threshold:.1f}%)"
            )
            if not self.fan_currently_on:
                self.fan_currently_on = True
                fan_command = "on"
                fan_control_needed = True
                self.last_alert_time = now_time

                # Send initial Telegram alert
                alert_msg = (
                    f"🚨 <b>CẢNH BÁO MÔI TRƯỜNG PHÒNG GYM</b> 🚨\n\n"
                    f"🕒 <b>Thời gian:</b> <code>{now_str}</code>\n"
                    f"🌡️ <b>Nhiệt độ:</b> <b>{temperature:.1f}°C</b> (Ngưỡng: {self.temp_threshold:.1f}°C)\n"
                    f"💧 <b>Độ ẩm:</b> <b>{humidity:.1f}%</b> (Ngưỡng: {self.humidity_threshold:.1f}%)\n"
                    f"🌀 <b>Hành động:</b> Đã kích hoạt <b>BẬT QUẠT THÔNG GIÓ</b> tự động."
                )
                await self.notification_service.send_alert(alert_msg, force=True)
                logger.warning(f"Environmental alert triggered: {reason}")
            elif (now_time - self.last_alert_time) >= self.alert_reminder_interval:
                # Periodic reminder if conditions remain hazardous for a long time
                self.last_alert_time = now_time
                reminder_msg = (
                    f"⚠️ <b>NHẮC NHỞ: MÔI TRƯỜNG VẪN VƯỢT NGƯỠNG</b> ⚠️\n\n"
                    f"🕒 <b>Thời gian:</b> <code>{now_str}</code>\n"
                    f"🌡️ <b>Nhiệt độ:</b> <b>{temperature:.1f}°C</b> (Ngưỡng: {self.temp_threshold:.1f}°C)\n"
                    f"💧 <b>Độ ẩm:</b> <b>{humidity:.1f}%</b> (Ngưỡng: {self.humidity_threshold:.1f}%)\n"
                    f"🌀 <b>Trạng thái:</b> Quạt vẫn đang bật. Vui lòng kiểm tra phòng tập!"
                )
                await self.notification_service.send_alert(reminder_msg, force=True)
                logger.warning(f"Environmental alert reminder sent: {reason}")
        elif is_fully_recovered and self.fan_currently_on:
            self.fan_currently_on = False
            fan_command = "off"
            fan_control_needed = True
            reason = "Môi trường đã trở lại bình thường. Tắt quạt thông gió."

            # Send Telegram recovery notice
            recovery_msg = (
                f"✅ <b>MÔI TRƯỜNG ĐÃ ỔN ĐỊNH</b> ✅\n\n"
                f"🕒 <b>Thời gian:</b> <code>{now_str}</code>\n"
                f"Môi trường phòng gym đã hạ nhiệt an toàn:\n"
                f"🌡️ <b>Nhiệt độ:</b> {temperature:.1f}°C\n"
                f"💧 <b>Độ ẩm:</b> {humidity:.1f}%\n"
                f"🌀 <b>Hành động:</b> Đã gửi lệnh <b>TẮT QUẠT THÔNG GIÓ</b>."
            )
            await self.notification_service.send_alert(recovery_msg, force=False)
            logger.info(f"Environment restored to normal: {reason}")

        # Save reading to repo
        reading = EnvironmentReading(
            temperature=temperature,
            humidity=humidity,
            fan_on=self.fan_currently_on,
            timestamp=now_iso,
        )
        saved_reading = await self.repository.add_environment_reading(reading)

        return {
            "fan_control_needed": fan_control_needed,
            "fan_command": fan_command,
            "reason": reason,
            "reading": saved_reading,
            "manual_mode": False,
        }

    async def set_fan_state(
        self,
        fan_on: bool,
        manual: bool = True,
        reason: str = "Manual control by Admin"
    ) -> EnvironmentReading:
        """Manually set fan state and record reading.

        If manual is True, enables manual mode so sensor readings will not override this state.
        """
        from datetime import datetime
        self.fan_currently_on = fan_on
        if manual:
            self.manual_mode = True
            self.manual_fan_state = fan_on
            logger.info(f"Fan manual mode enabled by Admin: fan_on={fan_on}")

        latest = await self.get_latest_reading()
        temp = latest.temperature if latest else 25.0
        humidity = latest.humidity if latest else 50.0

        reading = EnvironmentReading(
            temperature=temp,
            humidity=humidity,
            fan_on=self.fan_currently_on,
            timestamp=datetime.now().isoformat(),
        )
        saved_reading = await self.repository.add_environment_reading(reading)
        return saved_reading

    async def set_auto_mode(self) -> Dict[str, Any]:
        """Switch fan back to automatic threshold-controlled mode and re-evaluate."""
        self.manual_mode = False
        self.manual_fan_state = None
        logger.info("Fan control returned to AUTO mode by Admin.")

        latest = await self.get_latest_reading()
        if latest:
            return await self.process_reading(latest.temperature, latest.humidity)
        return {
            "fan_control_needed": False,
            "fan_command": None,
            "reason": "Chuyển về chế độ Tự động (AUTO)",
            "reading": None,
            "manual_mode": False,
        }

    async def get_latest_reading(self) -> Optional[EnvironmentReading]:
        """Fetch latest environment reading."""
        return await self.repository.get_latest_reading()

    async def get_history(self, limit: int = 50):
        """Fetch historical readings."""
        return await self.repository.get_environment_readings(limit=limit)

    def update_thresholds(self, temp_threshold: float, humidity_threshold: float) -> dict:
        """Update temperature and humidity thresholds at runtime."""
        self.temp_threshold = temp_threshold
        self.humidity_threshold = humidity_threshold
        logger.info(f"Environment thresholds updated: temp={self.temp_threshold}°C, humidity={self.humidity_threshold}%")
        return {
            "temp_threshold": self.temp_threshold,
            "humidity_threshold": self.humidity_threshold,
        }

    def get_thresholds(self) -> dict:
        """Get current threshold values."""
        return {
            "temp_threshold": self.temp_threshold,
            "humidity_threshold": self.humidity_threshold,
        }


