"""REST API routes for locker status."""

from typing import List
from fastapi import APIRouter, Request
from app.models.locker import Locker

router = APIRouter(prefix="/api/lockers", tags=["Lockers"])


@router.get("", response_model=List[Locker])
async def get_lockers(request: Request):
    """Retrieve status of all gym lockers."""
    locker_service = request.app.state.locker_service
    return await locker_service.get_all_lockers()
