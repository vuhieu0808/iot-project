"""REST API routes for locker status and admin control."""

from typing import List
from fastapi import APIRouter, HTTPException, Request, status
from pydantic import BaseModel, Field
from app.models.locker import Locker, LockerStatus
from app.api.websocket import ws_manager

router = APIRouter(prefix="/api/lockers", tags=["Lockers"])


class ForceAssignRequest(BaseModel):
    card_id: str = Field(..., description="RFID Card ID to assign to locker")


class LockerStatusRequest(BaseModel):
    status: LockerStatus = Field(..., description="New status for locker: vacant, occupied, or broken")


async def _broadcast_locker_update(locker_service):
    """Helper to broadcast updated locker list to WebSocket clients."""
    all_lockers = await locker_service.get_all_lockers()
    await ws_manager.broadcast({
        "type": "locker_event",
        "data": {
            "lockers": [l.model_dump() for l in all_lockers]
        }
    })


@router.get("", response_model=List[Locker])
async def get_lockers(request: Request):
    """Retrieve status of all gym lockers."""
    locker_service = request.app.state.locker_service
    return await locker_service.get_all_lockers()


@router.post("/{locker_number}/force-release", response_model=Locker)
async def force_release_locker(locker_number: int, request: Request):
    """Admin force release/unlock a locker."""
    locker_service = request.app.state.locker_service
    try:
        updated = await locker_service.force_release_locker(locker_number)
        await _broadcast_locker_update(locker_service)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{locker_number}/force-assign", response_model=Locker)
async def force_assign_locker(locker_number: int, body: ForceAssignRequest, request: Request):
    """Admin force assign a specific card_id to a locker."""
    locker_service = request.app.state.locker_service
    try:
        updated = await locker_service.force_assign_locker(locker_number, body.card_id)
        await _broadcast_locker_update(locker_service)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.patch("/{locker_number}/status", response_model=Locker)
async def set_locker_status(locker_number: int, body: LockerStatusRequest, request: Request):
    """Admin update status of a locker (vacant/occupied/broken)."""
    locker_service = request.app.state.locker_service
    try:
        updated = await locker_service.set_locker_status(locker_number, body.status)
        await _broadcast_locker_update(locker_service)
        return updated
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

