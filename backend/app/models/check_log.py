"""Check-in and check-out event log models."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class AccessAction(str, Enum):
    """Door access action enum."""
    CHECKIN = "checkin"
    CHECKOUT = "checkout"


class AccessStatus(str, Enum):
    """Access scan decision status."""
    GRANTED = "granted"
    DENIED = "denied"


class CheckLog(BaseModel):
    """Access log entry."""
    id: Optional[str] = Field(None, description="Log entry identifier")
    card_id: str = Field(..., description="Card ID scanned")
    member_name: str = Field("Unknown", description="Name of member")
    action: AccessAction = Field(..., description="Check-in or check-out")
    status: AccessStatus = Field(AccessStatus.GRANTED, description="Granted or denied")
    reason: Optional[str] = Field(None, description="Explanation if denied or details")
    duration_minutes: Optional[float] = Field(None, description="Session duration in minutes (populated on checkout)")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of event")
