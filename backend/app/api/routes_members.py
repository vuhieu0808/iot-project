"""REST API routes for member management."""

from typing import List
from fastapi import APIRouter, HTTPException, Request, status
from app.models.member import Member, MemberCreate

router = APIRouter(prefix="/api/members", tags=["Members"])


@router.get("", response_model=List[Member])
async def get_members(request: Request):
    """Retrieve list of all gym members."""
    repo = request.app.state.repository
    return await repo.get_all_members()


@router.post("", response_model=Member, status_code=status.HTTP_201_CREATED)
async def create_or_update_member(member_in: MemberCreate, request: Request):
    """Register or update member details."""
    repo = request.app.state.repository
    member = Member(**member_in.model_dump())
    saved = await repo.save_member(member)
    return saved


@router.get("/{card_id}", response_model=Member)
async def get_member_by_id(card_id: str, request: Request):
    """Retrieve details for a specific member by RFID card ID."""
    repo = request.app.state.repository
    member = await repo.get_member(card_id)
    if not member:
        raise HTTPException(status_code=404, detail=f"Member with card_id '{card_id}' not found.")
    return member


@router.delete("/{card_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_member(card_id: str, request: Request):
    """Delete a member record."""
    repo = request.app.state.repository
    deleted = await repo.delete_member(card_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Member with card_id '{card_id}' not found.")
