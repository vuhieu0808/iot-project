"""MQTT message routing and service invocation handlers."""

import json
import logging
from typing import Any, Callable, Dict, Optional

from app.mqtt.topics import Topics
from app.services.access_service import AccessService
from app.services.locker_service import LockerService
from app.services.environment_service import EnvironmentService

logger = logging.getLogger(__name__)


class MQTTMessageHandler:
    """Dispatches incoming MQTT messages to service logic and broadcasts WebSocket updates."""

    def __init__(
        self,
        access_service: AccessService,
        locker_service: LockerService,
        environment_service: EnvironmentService,
        publish_func: Callable[[str, str], None],
        broadcast_ws_func: Optional[Callable[[Dict[str, Any]], None]] = None,
    ):
        self.access_service = access_service
        self.locker_service = locker_service
        self.environment_service = environment_service
        self.publish = publish_func
        self.broadcast_ws = broadcast_ws_func

    async def handle_message(self, topic: str, payload_str: str) -> None:
        """Route topic message to correct handler."""
        logger.info(f"MQTT Received [{topic}]: {payload_str}")
        try:
            payload = json.loads(payload_str)
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON payload received on topic {topic}: '{payload_str}'")
            return

        if topic == Topics.DOOR_CHECKIN_REQUEST:
            await self._handle_checkin_request(payload)
        elif topic == Topics.LOCKER_REQUEST:
            await self._handle_locker_request(payload)
        elif topic == Topics.ENVIRONMENT_READING:
            await self._handle_environment_reading(payload)
        else:
            logger.warning(f"No handler registered for topic: {topic}")

    async def _handle_checkin_request(self, payload: Dict[str, Any]) -> None:
        """Process door card scan request."""
        card_id = payload.get("card_id")
        if not card_id:
            logger.error("Missing card_id in checkin request payload.")
            return

        result = await self.access_service.verify_card_scan(card_id)

        # Publish response to ESP32
        response_payload = json.dumps(result)
        self.publish(Topics.DOOR_CHECKIN_RESPONSE, response_payload)
        logger.info(f"Published checkin response to ESP32: {response_payload}")

        # Broadcast update to WebSocket clients
        if self.broadcast_ws:
            await self.broadcast_ws({
                "type": "checkin_event",
                "data": result
            })

    async def _handle_locker_request(self, payload: Dict[str, Any]) -> None:
        """Process locker card scan request."""
        card_id = payload.get("card_id")
        if not card_id:
            logger.error("Missing card_id in locker request payload.")
            return

        result = await self.locker_service.process_locker_scan(card_id)

        # Publish response to ESP32
        response_payload = json.dumps(result)
        self.publish(Topics.LOCKER_RESPONSE, response_payload)
        logger.info(f"Published locker response to ESP32: {response_payload}")

        # Broadcast update to WebSocket clients
        if self.broadcast_ws:
            all_lockers = await self.locker_service.get_all_lockers()
            await self.broadcast_ws({
                "type": "locker_event",
                "data": {
                    "event": result,
                    "lockers": [l.model_dump() for l in all_lockers]
                }
            })

    async def _handle_environment_reading(self, payload: Dict[str, Any]) -> None:
        """Process temperature and humidity sensor payload."""
        temp = payload.get("temperature")
        humidity = payload.get("humidity")

        if temp is None or humidity is None:
            logger.error("Missing temperature or humidity in environment reading payload.")
            return

        try:
            temp = float(temp)
            humidity = float(humidity)
        except ValueError:
            logger.error(f"Invalid non-numeric temp or humidity: {temp}, {humidity}")
            return

        result = await self.environment_service.process_reading(temp, humidity)

        # If fan state changed, publish fan control command to ESP32
        if result["fan_control_needed"]:
            fan_payload = json.dumps({
                "fan": result["fan_command"],
                "reason": result["reason"]
            })
            self.publish(Topics.ENVIRONMENT_FAN_CONTROL, fan_payload)
            logger.info(f"Published fan control to ESP32: {fan_payload}")

        # Broadcast update to WebSocket clients
        if self.broadcast_ws:
            reading: EnvironmentReading = result["reading"]
            await self.broadcast_ws({
                "type": "environment_update",
                "data": reading.model_dump()
            })
