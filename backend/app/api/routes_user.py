"""Member personal authenticated REST API routes for User Portal."""

from typing import List, Optional
from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from app.api.auth import create_user_token, hash_password, require_user, verify_password
from app.models.check_log import CheckLog
from app.models.locker import Locker

router = APIRouter(prefix="/api/user", tags=["User Portal"])


class UserLoginRequest(BaseModel):
    """User authentication login request."""
    card_id: str = Field(..., description="RFID Card ID")
    password: str = Field(..., description="Member password")


class UserLoginResponse(BaseModel):
    """User authentication login response containing JWT token."""
    token: str = Field(..., description="JWT Bearer authorization token")
    card_id: str = Field(..., description="Authenticated member card_id")
    name: str = Field(..., description="Authenticated member name")


class ChangePasswordRequest(BaseModel):
    """User change password request."""
    old_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=4, description="New password")


class MemberProfileResponse(BaseModel):
    """Member public profile response."""
    card_id: str
    name: str
    membership_expiry: date
    is_active: bool
    is_expired: bool


class UserStatsResponse(BaseModel):
    """Summary of member gym sessions and exercise duration."""
    total_sessions: int = Field(0, description="Total completed check-in sessions")
    total_workout_minutes: float = Field(0.0, description="Cumulative workout duration in minutes")


@router.post("/login", response_model=UserLoginResponse)
async def user_login(body: UserLoginRequest, request: Request):
    """Authenticate member by Card ID and password."""
    repo = request.app.state.repository
    member = await repo.get_member(body.card_id)
    if not member:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Tài khoản (Card ID) không tồn tại trong hệ thống",
        )

    if not member.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tài khoản thành viên đang bị tạm khóa",
        )

    if not verify_password(body.password, member.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Mật khẩu không chính xác. Mật khẩu mặc định ban đầu là '123456'",
        )

    token = create_user_token(member.card_id)
    return UserLoginResponse(token=token, card_id=member.card_id, name=member.name)


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_user_password(
    body: ChangePasswordRequest,
    request: Request,
    card_id: str = Depends(require_user),
):
    """Change member password (Requires User Auth Token)."""
    repo = request.app.state.repository
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail="Không tìm thấy thông tin thành viên")

    if not verify_password(body.old_password, member.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mật khẩu hiện tại không chính xác",
        )

    new_hash = hash_password(body.new_password)
    updated_member = member.model_copy(update={"password_hash": new_hash})
    await repo.save_member(updated_member)

    return {"message": "Đổi mật khẩu thành công!"}


@router.get("/me/profile", response_model=MemberProfileResponse)
async def get_my_profile(request: Request, card_id: str = Depends(require_user)):
    """Get profile of currently logged-in member."""
    repo = request.app.state.repository
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Card ID '{card_id}' not found.")

    today = date.today()
    is_expired = member.membership_expiry < today

    return MemberProfileResponse(
        card_id=member.card_id,
        name=member.name,
        membership_expiry=member.membership_expiry,
        is_active=member.is_active,
        is_expired=is_expired,
    )


@router.get("/me/history", response_model=List[CheckLog])
async def get_my_check_history(
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Max history records"),
    card_id: str = Depends(require_user),
):
    """Retrieve check-in / check-out logs for currently logged-in member."""
    repo = request.app.state.repository
    return await repo.get_check_logs(limit=limit, card_id=card_id)


@router.get("/me/locker", response_model=Optional[Locker])
async def get_my_assigned_locker(request: Request, card_id: str = Depends(require_user)):
    """Get locker currently held by logged-in member, or null if none."""
    repo = request.app.state.repository
    return await repo.get_locker_by_card(card_id)


@router.get("/me/stats", response_model=UserStatsResponse)
async def get_my_workout_stats(request: Request, card_id: str = Depends(require_user)):
    """Calculate workout session totals for logged-in member."""
    repo = request.app.state.repository
    logs = await repo.get_check_logs(limit=500, card_id=card_id)

    total_sessions = sum(1 for log in logs if log.action.value == "checkin" and log.status.value == "granted")
    total_minutes = sum(log.duration_minutes or 0.0 for log in logs if log.duration_minutes)

    return UserStatsResponse(
        total_sessions=total_sessions,
        total_workout_minutes=round(total_minutes, 1),
    )


# --- Legacy / Direct Card ID Endpoints (Kept for compatibility) ---

@router.get("/{card_id}/profile", response_model=MemberProfileResponse)
async def get_user_profile(card_id: str, request: Request):
    """Query member status and expiration date by card_id."""
    repo = request.app.state.repository
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"No member profile registered for Card ID '{card_id}'.")

    today = date.today()
    is_expired = member.membership_expiry < today

    return MemberProfileResponse(
        card_id=member.card_id,
        name=member.name,
        membership_expiry=member.membership_expiry,
        is_active=member.is_active,
        is_expired=is_expired,
    )


@router.get("/{card_id}/history", response_model=List[CheckLog])
async def get_user_check_history(
    card_id: str,
    request: Request,
    limit: int = Query(50, ge=1, le=200, description="Max history records"),
):
    """Retrieve check-in / check-out logs for specified card_id."""
    repo = request.app.state.repository
    return await repo.get_check_logs(limit=limit, card_id=card_id)


@router.get("/{card_id}/locker", response_model=Optional[Locker])
async def get_user_assigned_locker(card_id: str, request: Request):
    """Get locker currently held by member card_id, or null if none."""
    repo = request.app.state.repository
    return await repo.get_locker_by_card(card_id)


@router.get("/{card_id}/stats", response_model=UserStatsResponse)
async def get_user_workout_stats(card_id: str, request: Request):
    """Calculate workout session totals for specified card_id."""
    repo = request.app.state.repository
    logs = await repo.get_check_logs(limit=500, card_id=card_id)

    total_sessions = sum(1 for log in logs if log.action.value == "checkin" and log.status.value == "granted")
    total_minutes = sum(log.duration_minutes or 0.0 for log in logs if log.duration_minutes)

    return UserStatsResponse(
        total_sessions=total_sessions,
        total_workout_minutes=round(total_minutes, 1),
    )
