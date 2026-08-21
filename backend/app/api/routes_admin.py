"""Admin management REST API routes requiring JWT authentication."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.config import settings
from app.api.auth import create_admin_token, require_admin
from app.models.member import Member, MemberCreate
from app.models.locker import Locker, LockerStatus, LockerLog
from app.models.check_log import CheckLog
from app.models.environment import EnvironmentReading
from app.api.websocket import ws_manager

router = APIRouter(prefix="/api/admin", tags=["Admin Management"])


class AdminLoginRequest(BaseModel):
    """Admin login credentials request model."""
    username: str = Field(..., description="Admin username")
    password: str = Field(..., description="Admin password")


class AdminLoginResponse(BaseModel):
    """Admin login authentication response containing JWT token."""
    token: str = Field(..., description="JWT Bearer authorization token")
    username: str = Field(..., description="Authenticated username")


class ForceAssignRequest(BaseModel):
    """Admin force assign locker request model."""
    card_id: str = Field(..., description="RFID Card ID to assign to locker")


class LockerStatusRequest(BaseModel):
    """Admin status change request model."""
    status: LockerStatus = Field(..., description="New status for locker")


class FanControlRequest(BaseModel):
    """Admin fan control command request model."""
    command: str = Field(..., description="Fan command: 'on', 'off', or 'auto'")


class ThresholdUpdateRequest(BaseModel):
    """Admin threshold update request model."""
    temp_threshold: float = Field(..., ge=0, le=100, description="Temperature threshold in Celsius")
    humidity_threshold: float = Field(..., ge=0, le=100, description="Humidity threshold in percentage")


class ThresholdResponse(BaseModel):
    """Current environment threshold values response."""
    temp_threshold: float
    humidity_threshold: float



async def _broadcast_admin_locker_update(locker_service):
    """Broadcast updated full lockers and logs to admin WS clients & status to public WS clients."""
    all_lockers = await locker_service.get_all_lockers()
    recent_logs = await locker_service.get_locker_logs(limit=20)
    await ws_manager.broadcast_admin({
        "type": "locker_event",
        "data": {
            "lockers": [l.model_dump() for l in all_lockers],
            "recent_logs": [log.model_dump() for log in recent_logs],
        }
    })
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


@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(body: AdminLoginRequest):
    """Authenticate admin credentials and return JWT bearer token."""
    if body.username == settings.ADMIN_USERNAME and body.password == settings.ADMIN_PASSWORD:
        token = create_admin_token(body.username)
        return AdminLoginResponse(token=token, username=body.username)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid admin username or password",
    )


@router.get("/activity", response_model=List[CheckLog])
async def get_admin_activity_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=500, description="Max history records"),
    card_id: Optional[str] = Query(None, description="Optional card_id filter"),
    _: str = Depends(require_admin),
):
    """Retrieve complete real-time RFID check-in/out activity logs (Admin Auth Required)."""
    repo = request.app.state.repository
    return await repo.get_check_logs(limit=limit, card_id=card_id)


@router.get("/lockers", response_model=List[Locker])
async def get_admin_lockers(
    request: Request,
    _: str = Depends(require_admin),
):
    """Retrieve detailed state of all lockers including assigned card_ids (Admin Auth Required)."""
    locker_service = request.app.state.locker_service
    return await locker_service.get_all_lockers()


@router.get("/lockers/logs", response_model=List[LockerLog])
async def get_admin_locker_logs(
    request: Request,
    limit: int = Query(100, ge=1, le=500, description="Max history records"),
    locker_number: Optional[int] = Query(None, description="Optional locker_number filter"),
    card_id: Optional[str] = Query(None, description="Optional card_id filter"),
    _: str = Depends(require_admin),
):
    """Retrieve complete locker activity logs (Admin Auth Required)."""
    locker_service = request.app.state.locker_service
    return await locker_service.get_locker_logs(limit=limit, locker_number=locker_number, card_id=card_id)


@router.post("/lockers/{locker_number}/force-release", response_model=Locker)
async def force_release_locker(
    locker_number: int,
    request: Request,
    _: str = Depends(require_admin),
):
    """Admin force release/unlock a locker (Admin Auth Required)."""
    locker_service = request.app.state.locker_service
    try:
        updated = await locker_service.force_release_locker(locker_number)
        await _broadcast_admin_locker_update(locker_service)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/lockers/{locker_number}/force-assign", response_model=Locker)
async def force_assign_locker(
    locker_number: int,
    body: ForceAssignRequest,
    request: Request,
    _: str = Depends(require_admin),
):
    """Admin force assign a specific card_id to a locker (Admin Auth Required)."""
    locker_service = request.app.state.locker_service
    try:
        updated = await locker_service.force_assign_locker(locker_number, body.card_id)
        await _broadcast_admin_locker_update(locker_service)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/lockers/{locker_number}/status", response_model=Locker)
async def set_locker_status(
    locker_number: int,
    body: LockerStatusRequest,
    request: Request,
    _: str = Depends(require_admin),
):
    """Admin update locker status: vacant, occupied, or broken (Admin Auth Required)."""
    locker_service = request.app.state.locker_service
    try:
        updated = await locker_service.set_locker_status(locker_number, body.status)
        await _broadcast_admin_locker_update(locker_service)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/members", response_model=List[Member])
async def get_admin_members(
    request: Request,
    _: str = Depends(require_admin),
):
    """Retrieve full list of registered gym members (Admin Auth Required)."""
    repo = request.app.state.repository
    return await repo.get_all_members()


@router.post("/members", response_model=Member, status_code=status.HTTP_201_CREATED)
async def save_admin_member(
    member_in: MemberCreate,
    request: Request,
    _: str = Depends(require_admin),
):
    """Create or update a member record (Admin Auth Required)."""
    repo = request.app.state.repository
    from app.api.auth import hash_password

    existing = await repo.get_member(member_in.card_id)
    pw_hash = None
    if member_in.password:
        pw_hash = hash_password(member_in.password)
    elif not existing:
        # Default initial password for new members: "123456"
        pw_hash = hash_password("123456")
    else:
        pw_hash = existing.password_hash

    member_dict = member_in.model_dump(exclude={"password"})
    member = Member(**member_dict, password_hash=pw_hash)
    return await repo.save_member(member)


@router.post("/members/{card_id}/reset-password")
async def reset_admin_member_password(
    card_id: str,
    request: Request,
    _: str = Depends(require_admin),
):
    """Reset a member's password to default '123456' (Admin Auth Required)."""
    repo = request.app.state.repository
    from app.api.auth import hash_password
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Member with card_id '{card_id}' not found.")

    default_hash = hash_password("123456")
    updated = member.model_copy(update={"password_hash": default_hash})
    await repo.save_member(updated)
    return {"message": f"Đã reset mật khẩu của thành viên '{card_id}' về mặc định: 123456"}


@router.get("/members/{card_id}", response_model=Member)
async def get_admin_member_by_id(
    card_id: str,
    request: Request,
    _: str = Depends(require_admin),
):
    """Retrieve details for a specific member by RFID card ID (Admin Auth Required)."""
    repo = request.app.state.repository
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Member with card_id '{card_id}' not found.")
    return member


@router.delete("/members/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_admin_member(
    card_id: str,
    request: Request,
    _: str = Depends(require_admin),
):
    """Delete a member record (Admin Auth Required)."""
    repo = request.app.state.repository
    deleted = await repo.delete_member(card_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Member with card_id '{card_id}' not found.")


@router.post("/members/{card_id}/toggle-active", response_model=Member)
async def toggle_admin_member_active(
    card_id: str,
    request: Request,
    is_active: Optional[bool] = Query(None, description="Optional target active state; toggles if omitted"),
    _: str = Depends(require_admin),
):
    """Toggle or set active status of a gym member (Admin Auth Required)."""
    repo = request.app.state.repository
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Member with card_id '{card_id}' not found.")

    new_active = not member.is_active if is_active is None else is_active
    updated_member = member.model_copy(update={"is_active": new_active})
    return await repo.save_member(updated_member)


@router.get("/environment/history", response_model=List[EnvironmentReading])
async def get_admin_environment_history(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Max history records"),
    _: str = Depends(require_admin),
):
    """Get detailed historical environment sensor readings (Admin Auth Required)."""
    env_service = request.app.state.environment_service
    return await env_service.get_history(limit=limit)


@router.post("/environment/fan")
async def control_admin_fan(
    body: FanControlRequest,
    request: Request,
    _: str = Depends(require_admin),
):
    """Manually turn ventilation fan ON, OFF, or switch to AUTO mode (Admin Auth Required)."""
    if body.command not in ["on", "off", "auto"]:
        raise HTTPException(status_code=400, detail="Command must be 'on', 'off', or 'auto'.")

    env_service = request.app.state.environment_service
    mqtt_client = request.app.state.mqtt_client
    from app.mqtt.topics import Topics
    import json

    if body.command == "auto":
        # 1. Return to AUTO mode and re-evaluate with current sensor reading
        result = await env_service.set_auto_mode()
        fan_on = env_service.fan_currently_on
        reading = result.get("reading") or await env_service.get_latest_reading()

        # 2. Publish MQTT command if fan state needs to change
        if result.get("fan_control_needed") and result.get("fan_command"):
            fan_payload = json.dumps({
                "fan": result["fan_command"],
                "reason": "Chuyển về chế độ Tự động (AUTO) bởi Admin"
            })
            mqtt_client.publish(Topics.ENVIRONMENT_FAN_CONTROL, fan_payload)

        # 3. Broadcast WS update to all clients
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
        # 1. Update service internal state & set manual override to True (Highest priority)
        reading = await env_service.set_fan_state(
            fan_on=fan_on,
            manual=True,
            reason=f"Lệnh thủ công ({body.command.upper()}) bởi Admin (Ưu tiên cao nhất)"
        )

        # 2. Publish MQTT command to ESP32
        fan_payload = json.dumps({
            "fan": body.command,
            "reason": f"Lệnh thủ công ({body.command.upper()}) bởi Admin"
        })
        mqtt_client.publish(Topics.ENVIRONMENT_FAN_CONTROL, fan_payload)

        # 3. Broadcast WS update to all clients
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



@router.get("/environment/thresholds", response_model=ThresholdResponse)
async def get_environment_thresholds(
    request: Request,
    _: str = Depends(require_admin),
):
    """Get current environment threshold settings (Admin Auth Required)."""
    env_service = request.app.state.environment_service
    return env_service.get_thresholds()


@router.put("/environment/thresholds", response_model=ThresholdResponse)
async def update_environment_thresholds(
    body: ThresholdUpdateRequest,
    request: Request,
    _: str = Depends(require_admin),
):
    """Update environment thresholds for automatic fan control (Admin Auth Required)."""
    env_service = request.app.state.environment_service
    repo = request.app.state.repository

    # 1. Update service runtime state
    updated = env_service.update_thresholds(body.temp_threshold, body.humidity_threshold)

    # 2. Persist to repository/Firebase
    await repo.save_environment_thresholds(body.temp_threshold, body.humidity_threshold)

    # 3. Broadcast threshold change via WebSocket to admin clients
    await ws_manager.broadcast_admin({
        "type": "threshold_update",
        "data": updated
    })

    return updated


@router.post("/telegram/test")
async def test_telegram_alert(
    request: Request,
    _: str = Depends(require_admin),
):
    """Send a test notification to configured Telegram Chat ID (Admin Auth Required)."""
    notif_service = request.app.state.notification_service
    if not notif_service or not notif_service.is_configured:
        raise HTTPException(
            status_code=400,
            detail="Telegram Bot Token hoặc Chat ID chưa được cấu hình trong file .env.",
        )

    from datetime import datetime
    now_str = datetime.now().strftime("%H:%M:%S %d/%m/%Y")
    test_msg = (
        f"🔔 <b>THỬ NGHIỆM THÔNG BÁO GYMTAG</b> 🔔\n\n"
        f"🕒 <b>Thời gian:</b> <code>{now_str}</code>\n"
        f"✅ Hệ thống GymTag kết nối thành công tới Telegram Bot!\n"
        f"Cảnh báo nhiệt độ, độ ẩm và sự cố sẽ được gửi tức thì đến kênh này."
    )
    success = await notif_service.send_alert(test_msg, force=True)
    if not success:
        raise HTTPException(
            status_code=502,
            detail="Gửi thông báo Telegram thất bại. Vui lòng kiểm tra lại Bot Token, Chat ID hoặc kết nối mạng.",
        )

    return {"message": "Đã gửi thông báo thử nghiệm tới Telegram thành công!"}

