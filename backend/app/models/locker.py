"""Locker data model."""

from pydantic import BaseModel, Field
from typing import Optional


class Locker(BaseModel):
    """Locker state representation."""
    locker_number: int = Field(..., description="Locker slot number (1-N)")
    is_occupied: bool = Field(False, description="Whether locker is occupied")
    card_id: Optional[str] = Field(None, description="Card ID currently holding the locker")
    assigned_at: Optional[str] = Field(None, description="ISO timestamp when locker was assigned")
