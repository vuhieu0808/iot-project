"""MQTT Client wrapper using paho-mqtt."""

import asyncio
import logging
from typing import Callable, Optional
import paho.mqtt.client as mqtt

from app.mqtt.topics import Topics

logger = logging.getLogger(__name__)


class MQTTClient:
    """Wrapper managing MQTT broker connection, subscription, and thread-safe asyncio message handling."""

    def __init__(
        self,
        broker: str,
        port: int = 1883,
        username: Optional[str] = None,
        password: Optional[str] = None,
        client_id: str = "gymtag_backend",
    ):
        self.broker = broker
        self.port = port
        self.username = username
        self.password = password
        self.client_id = client_id

        self.client = mqtt.Client(client_id=self.client_id)
        if self.username and self.password:
            self.client.username_pw_set(self.username, self.password)

        self.client.on_connect = self._on_connect
        self.client.on_disconnect = self._on_disconnect
        self.client.on_message = self._on_message

        self._async_handler: Optional[Callable] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None

    def set_async_handler(self, handler_coro: Callable, loop: asyncio.AbstractEventLoop) -> None:
        """Register async handler function and loop."""
        self._async_handler = handler_coro
        self._loop = loop

    def connect(self) -> None:
        """Connect to MQTT broker and start background network thread."""
        logger.info(f"Connecting to MQTT broker at {self.broker}:{self.port}...")
        try:
            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")

    def disconnect(self) -> None:
        """Stop network loop and disconnect."""
        logger.info("Disconnecting MQTT client...")
        try:
            self.client.loop_stop()
            self.client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting MQTT client: {e}")

    def publish(self, topic: str, payload: str) -> None:
        """Publish payload to MQTT topic."""
        try:
            res = self.client.publish(topic, payload)
            if res.rc != mqtt.MQTT_ERR_SUCCESS:
                logger.error(f"MQTT publish failed with code {res.rc} on topic {topic}")
        except Exception as e:
            logger.error(f"Error publishing to MQTT topic {topic}: {e}")

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            logger.info("Connected to MQTT broker successfully.")
            # Subscribe to incoming ESP32 topics
            topics_to_subscribe = [
                (Topics.DOOR_CHECKIN_REQUEST, 0),
                (Topics.DOOR_CHECKOUT_REQUEST, 0),
                (Topics.LOCKER_REQUEST, 0),
                (Topics.ENVIRONMENT_READING, 0),
                (Topics.REPS_COUNTER_REQUEST, 0),
                (Topics.REPS_COUNTER_RESULT, 0),
            ]
            self.client.subscribe(topics_to_subscribe)
            logger.info(f"Subscribed to topics: {[t[0] for t in topics_to_subscribe]}")
        else:
            logger.error(f"MQTT Connection failed with return code {rc}")

    def _on_disconnect(self, client, userdata, rc):
        if rc != 0:
            logger.warning(f"Unexpected MQTT disconnection (rc={rc}). Will attempt reconnection.")

    def _on_message(self, client, userdata, msg):
        topic = msg.topic
        payload = msg.payload.decode("utf-8", errors="ignore")

        if self._async_handler and self._loop and self._loop.is_running():
            asyncio.run_coroutine_threadsafe(
                self._async_handler(topic, payload),
                self._loop
            )
        else:
            logger.warning("Received MQTT message but async handler loop is not ready.")
