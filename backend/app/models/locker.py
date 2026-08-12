"""Locker data model."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class LockerStatus(str, Enum):
    """Locker state enum."""
    VACANT = "vacant"
    OCCUPIED = "occupied"
    BROKEN = "broken"


class Locker(BaseModel):
    """Locker state representation."""
    locker_number: int = Field(..., description="Locker slot number (1-N)")
    status: LockerStatus = Field(LockerStatus.VACANT, description="Detailed locker status")
    is_occupied: bool = Field(False, description="Whether locker is occupied (computed / backward compatibility)")
    card_id: Optional[str] = Field(None, description="Card ID currently holding the locker")
    assigned_at: Optional[str] = Field(None, description="ISO timestamp when locker was assigned")

    def model_post_init(self, __context):
        # Ensure is_occupied is synced with status if status is provided, or vice versa
        if self.status == LockerStatus.OCCUPIED:
            self.is_occupied = True
        elif self.status in (LockerStatus.VACANT, LockerStatus.BROKEN):
            self.is_occupied = False

