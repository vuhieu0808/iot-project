"""REST API routes for environmental sensor telemetry."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.models.environment import EnvironmentReading

router = APIRouter(prefix="/api/environment", tags=["Environment"])


class FanControlRequest(BaseModel):
    """Fan control command request model."""
    command: str = Field(..., description="Fan command: 'on' or 'off'")


@router.get("/latest", response_model=Optional[EnvironmentReading])
async def get_latest_environment(request: Request):
    """Get the most recent temperature and humidity reading."""
    env_service = request.app.state.environment_service
    reading = await env_service.get_latest_reading()
    if not reading:
        raise HTTPException(status_code=404, detail="No environment readings recorded yet.")
    return reading


@router.get("/history", response_model=List[EnvironmentReading])
async def get_environment_history(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Max history records to return")
):
    """Get short-term environment telemetry history."""
    env_service = request.app.state.environment_service
    return await env_service.get_history(limit=limit)


@router.post("/fan")
async def control_fan(body: FanControlRequest, request: Request):
    """Manually turn ventilation fan ON or OFF."""
    if body.command not in ["on", "off"]:
        raise HTTPException(status_code=400, detail="Command must be 'on' or 'off'.")

    fan_on = (body.command == "on")
    env_service = request.app.state.environment_service
    mqtt_client = request.app.state.mqtt_client

    # 1. Update service internal state & log reading
    reading = await env_service.set_fan_state(fan_on, reason=f"Manual control ({body.command.upper()})")

    # 2. Publish MQTT command to ESP32
    from app.mqtt.topics import Topics
    import json
    fan_payload = json.dumps({
        "fan": body.command,
        "reason": "Manual control"
    })
    mqtt_client.publish(Topics.ENVIRONMENT_FAN_CONTROL, fan_payload)

    # 3. Broadcast WS update to all clients
    from app.api.websocket import ws_manager
    await ws_manager.broadcast({
        "type": "environment_update",
        "data": reading.model_dump()
    })

    return {
        "message": f"Đã gửi lệnh {body.command.upper()} quạt thông gió thành công!",
        "fan_on": fan_on,
        "reading": reading,
    }

