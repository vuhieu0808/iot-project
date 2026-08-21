"""Locker data model."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import Optional


class LockerStatus(str, Enum):
    """Locker state enum."""
    VACANT = "vacant"
    OCCUPIED = "occupied"
    BROKEN = "broken"


class LockerAction(str, Enum):
    """Locker event action enum."""
    ASSIGN = "assign"               # Cấp / Mượn tủ mới
    ACCESS = "access"               # Mở tủ đang giữ
    RELEASE = "release"             # Trả / Giải phóng tủ
    FORCE_ASSIGN = "force_assign"   # Admin ép gán tủ
    FORCE_RELEASE = "force_release" # Admin ép mở / giải phóng tủ
    STATUS_CHANGE = "status_change" # Admin đổi trạng thái (bảo trì/trống)
    DENIED = "denied"               # Từ chối thao tác / thẻ không hợp lệ


class LockerLogStatus(str, Enum):
    """Locker log outcome status."""
    GRANTED = "granted"
    DENIED = "denied"


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


class LockerLog(BaseModel):
    """Locker activity log entry."""
    id: Optional[str] = Field(None, description="Log entry identifier (UUID)")
    locker_number: Optional[int] = Field(None, description="Locker slot number (1-N)")
    card_id: Optional[str] = Field(None, description="Card ID involved in event")
    member_name: str = Field("Unknown", description="Name of member or Admin")
    action: LockerAction = Field(..., description="Locker action performed")
    status: LockerLogStatus = Field(LockerLogStatus.GRANTED, description="Outcome status")
    reason: Optional[str] = Field(None, description="Detailed explanation or outcome description")
    timestamp: Optional[str] = Field(None, description="ISO timestamp of event")

