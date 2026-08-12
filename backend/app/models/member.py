"""Member data models."""

from datetime import date
from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class MemberStatus(str, Enum):
    """Membership status enum."""
    VALID = "valid"
    EXPIRED = "expired"
    NOT_FOUND = "not_found"


class MemberCreate(BaseModel):
    """Schema for creating a new member."""
    card_id: str = Field(..., description="RFID card unique identifier")
    name: str = Field(..., description="Full name of member")
    email: Optional[str] = Field(None, description="Email address")
    phone: Optional[str] = Field(None, description="Phone number")
    membership_expiry: date = Field(..., description="Membership expiration date")
    is_active: bool = Field(True, description="Whether account is active")
    password: Optional[str] = Field(None, description="Initial plain password for user (optional, default 123456)")


class Member(MemberCreate):
    """Member model stored in system database."""
    created_at: Optional[str] = Field(None, description="ISO timestamp when registered")
    password_hash: Optional[str] = Field(None, description="Hashed password string")
