"""MQTT message routing and service invocation handlers."""

import json
import logging
from typing import Any, Callable, Dict, Optional

from app.mqtt.topics import Topics
from app.services.access_service import AccessService
from app.services.locker_service import LockerService
from app.services.environment_service import EnvironmentService
from app.services.occupancy_service import OccupancyService
from app.api.websocket import ws_manager

logger = logging.getLogger(__name__)


class MQTTMessageHandler:
    """Dispatches incoming MQTT messages to service logic and broadcasts WebSocket updates."""

    def __init__(
        self,
        access_service: AccessService,
        locker_service: LockerService,
        environment_service: EnvironmentService,
        occupancy_service: OccupancyService,
        publish_func: Callable[[str, str], None],
    ):
        self.access_service = access_service
        self.locker_service = locker_service
        self.environment_service = environment_service
        self.occupancy_service = occupancy_service
        self.publish = publish_func

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
        elif topic == Topics.DOOR_CHECKOUT_REQUEST:
            await self._handle_checkout_request(payload)
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

        result = await self.access_service.checkin(card_id)

        # Publish response to ESP32
        response_payload = json.dumps(result)
        self.publish(Topics.DOOR_CHECKIN_RESPONSE, response_payload)
        logger.info(f"Published checkin response to ESP32: {response_payload}")

        # Broadcast detailed check-in activity event to authenticated ADMIN WS clients
        await ws_manager.broadcast_admin({
            "type": "checkin_event",
            "data": result
        })

        # Broadcast updated occupancy count to PUBLIC WS clients
        occupancy_count = await self.occupancy_service.get_current_occupancy()
        await ws_manager.broadcast_public({
            "type": "occupancy_update",
            "data": {
                "current_occupancy": occupancy_count
            }
        })

    async def _handle_checkout_request(self, payload: Dict[str, Any]) -> None:
        card_id = payload.get("card_id")
        if not card_id:
            logger.error("Missing card_id in checkout request payload.")
            return

        result = await self.access_service.checkout(card_id)

        response_payload = json.dumps(result)
        self.publish(Topics.DOOR_CHECKOUT_RESPONSE, response_payload)
        logger.info(f"Published checkout response to ESP32: {response_payload}")

        await ws_manager.broadcast_admin({
            "type": "checkout_event",
            "data": result
        })

        occupancy_count = await self.occupancy_service.get_current_occupancy()
        await ws_manager.broadcast_public({
            "type": "occupancy_update",
            "data": {
                "current_occupancy": occupancy_count
            }
        })

    async def _handle_locker_request(self, payload: Dict[str, Any]) -> None:
        """Process locker card scan request."""
        card_id = payload.get("card_id")
        if not card_id:
            logger.error("Missing card_id in locker request payload.")
            return

        operation = payload.get("operation", "scan")
        if operation == "scan":
            result = await self.locker_service.process_locker_scan(card_id)
        elif operation == "release":
            locker_number = payload.get("locker_number")
            if not isinstance(locker_number, int) or isinstance(locker_number, bool) or locker_number <= 0:
                result = {
                    "card_id": card_id,
                    "action": "denied",
                    "locker_number": None,
                    "member_name": None,
                    "reason": "A valid locker_number is required for release",
                }
            else:
                result = await self.locker_service.release_locker(card_id, locker_number)
        else:
            result = {
                "card_id": card_id,
                "action": "denied",
                "locker_number": None,
                "member_name": None,
                "reason": f"Unsupported locker operation: {operation}",
            }

        # Publish response to ESP32
        response_payload = json.dumps(result)
        self.publish(Topics.LOCKER_RESPONSE, response_payload)
        logger.info(f"Published locker response to ESP32: {response_payload}")

        # Broadcast full detailed locker event to ADMIN WS clients
        all_lockers = await self.locker_service.get_all_lockers()
        recent_logs = await self.locker_service.get_locker_logs(limit=20)
        await ws_manager.broadcast_admin({
            "type": "locker_event",
            "data": {
                "event": result,
                "lockers": [l.model_dump() for l in all_lockers],
                "recent_logs": [log.model_dump() for log in recent_logs],
            }
        })

        # Broadcast privacy-safe locker status update to PUBLIC WS clients (omitting card_id)
        await ws_manager.broadcast_public({
            "type": "locker_status_update",
            "data": {
                "lockers": [
                    {
                        "locker_number": l.locker_number,
                        "status": l.status.value,
                        "is_occupied": l.is_occupied,
                    }
                    for l in all_lockers
                ]
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

        # Broadcast environment telemetry to ALL WebSocket clients (Public & Admin)
        reading = result["reading"]
        update_data = {
            **reading.model_dump(),
            "manual_mode": result.get("manual_mode", self.environment_service.manual_mode),
        }
        await ws_manager.broadcast({
            "type": "environment_update",
            "data": update_data
        })


