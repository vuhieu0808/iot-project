"""REST API routes for environmental sensor telemetry."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field
from app.models.environment import EnvironmentReading

router = APIRouter(prefix="/api/environment", tags=["Environment"])


class FanControlRequest(BaseModel):
    """Fan control command request model."""
    command: str = Field(..., description="Fan command: 'on', 'off', or 'auto'")


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
    """Manually turn ventilation fan ON, OFF, or switch to AUTO mode."""
    if body.command not in ["on", "off", "auto"]:
        raise HTTPException(status_code=400, detail="Command must be 'on', 'off', or 'auto'.")

    env_service = request.app.state.environment_service
    mqtt_client = request.app.state.mqtt_client
    from app.mqtt.topics import Topics
    from app.api.websocket import ws_manager
    import json

    if body.command == "auto":
        result = await env_service.set_auto_mode()
        fan_on = env_service.fan_currently_on
        reading = result.get("reading") or await env_service.get_latest_reading()

        if result.get("fan_control_needed") and result.get("fan_command"):
            fan_payload = json.dumps({
                "fan": result["fan_command"],
                "reason": "Chuyển về chế độ Tự động (AUTO)"
            })
            mqtt_client.publish(Topics.ENVIRONMENT_FAN_CONTROL, fan_payload)

        if reading:
            await ws_manager.broadcast({
                "type": "environment_update",
                "data": {
                    **reading.model_dump(),
                    "manual_mode": False,
                }
            })

        return {
            "message": "Đã chuyển quạt thông gió sang chế độ TỰ ĐỘNG (AUTO) thành công!",
            "fan_on": fan_on,
            "manual_mode": False,
            "reading": reading,
        }
    else:
        fan_on = (body.command == "on")
        reading = await env_service.set_fan_state(
            fan_on=fan_on,
            manual=True,
            reason=f"Lệnh thủ công ({body.command.upper()}) (Ưu tiên cao nhất)"
        )

        fan_payload = json.dumps({
            "fan": body.command,
            "reason": f"Manual control ({body.command.upper()})"
        })
        mqtt_client.publish(Topics.ENVIRONMENT_FAN_CONTROL, fan_payload)

        await ws_manager.broadcast({
            "type": "environment_update",
            "data": {
                **reading.model_dump(),
                "manual_mode": True,
            }
        })

        return {
            "message": f"Đã gửi lệnh {body.command.upper()} quạt thông gió (Thủ công - Ưu tiên cao nhất) thành công!",
            "fan_on": fan_on,
            "manual_mode": True,
            "reading": reading,
        }


