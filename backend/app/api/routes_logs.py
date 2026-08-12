"""REST API routes for check-in/out history logs and real-time occupancy."""

from typing import List, Optional
from fastapi import APIRouter, Query, Request
from app.models.check_log import CheckLog

router = APIRouter(tags=["Logs & Occupancy"])


@router.get("/api/logs", response_model=List[CheckLog])
async def get_check_logs(
    request: Request,
    limit: int = Query(50, ge=1, le=500, description="Max log records to return"),
    card_id: Optional[str] = Query(None, description="Filter by card_id")
):
    """Retrieve check-in / check-out history logs."""
    repo = request.app.state.repository
    return await repo.get_check_logs(limit=limit, card_id=card_id)


@router.get("/api/occupancy")
async def get_occupancy(request: Request):
    """Get real-time number of members currently inside the gym."""
    occ_service = request.app.state.occupancy_service
    count = await occ_service.get_current_occupancy()
    return {"current_occupancy": count}
