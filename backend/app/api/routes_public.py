"""Public REST API routes requiring no authentication."""

from typing import List, Optional
from fastapi import APIRouter, Request
from pydantic import BaseModel, Field
from app.models.locker import LockerStatus

router = APIRouter(prefix="/api/public", tags=["Public"])


class PublicLockerState(BaseModel):
    """Public locker view model omitting privacy-sensitive card_id."""
    locker_number: int = Field(..., description="Locker slot number")
    status: LockerStatus = Field(..., description="Locker status: vacant, occupied, broken")
    is_occupied: bool = Field(..., description="Whether locker is occupied")


class SystemStatusResponse(BaseModel):
    """Public gym system telemetry overview."""
    current_occupancy: int = Field(..., description="Current count of members in gym")
    temperature: Optional[float] = Field(None, description="Latest room temperature in Celsius")
    humidity: Optional[float] = Field(None, description="Latest relative humidity percentage")
    fan_on: bool = Field(False, description="Cooling fan state")


@router.get("/status", response_model=SystemStatusResponse)
async def get_public_status(request: Request):
    """Get aggregated gym occupancy and environment telemetry for public view."""
    occ_service = request.app.state.occupancy_service
    env_service = request.app.state.environment_service

    occupancy = await occ_service.get_current_occupancy()
    env_latest = await env_service.get_latest_reading()

    return SystemStatusResponse(
        current_occupancy=occupancy,
        temperature=env_latest.temperature if env_latest else None,
        humidity=env_latest.humidity if env_latest else None,
        fan_on=env_latest.fan_on if env_latest else False,
    )


@router.get("/lockers", response_model=List[PublicLockerState])
async def get_public_lockers(request: Request):
    """Get locker status grid without user card_ids."""
    locker_service = request.app.state.locker_service
    all_lockers = await locker_service.get_all_lockers()

    return [
        PublicLockerState(
            locker_number=l.locker_number,
            status=l.status,
            is_occupied=l.is_occupied,
        )
        for l in all_lockers
    ]
