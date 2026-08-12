"""Telegram alert notification service using httpx."""

import logging
import time
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class NotificationService:
    """Sends notification alerts to Telegram chat using standard Bot API HTTP requests."""

    def __init__(self, bot_token: Optional[str] = None, chat_id: Optional[str] = None):
        self.bot_token = bot_token
        self.chat_id = chat_id
        self.last_sent_time: float = 0.0
        self.last_message: str = ""
        self.cooldown_seconds: float = 60.0

    async def send_alert(self, message: str, force: bool = False) -> bool:
        """Send warning/alert message to Telegram chat.

        Args:
            message: Text message to send.
            force: If True, bypass cooldown check.

        Returns:
            bool: True if sent successfully, False otherwise.
        """
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram Bot Token or Chat ID not configured. Skipping notification.")
            return False

        now = time.time()
        if not force and message == self.last_message and (now - self.last_sent_time) < self.cooldown_seconds:
            logger.info("Telegram notification rate-limited (duplicate message sent recently).")
            return False

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML"
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload)
                if response.status_code == 200:
                    logger.info(f"Telegram alert sent successfully: '{message}'")
                    self.last_sent_time = now
                    self.last_message = message
                    return True
                else:
                    logger.error(f"Failed to send Telegram alert. HTTP {response.status_code}: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Error sending Telegram notification: {e}")
            return False
