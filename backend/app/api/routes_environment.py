"""REST API routes for environmental sensor telemetry."""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Request
from app.models.environment import EnvironmentReading

router = APIRouter(prefix="/api/environment", tags=["Environment"])


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
