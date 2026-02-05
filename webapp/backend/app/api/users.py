"""
User endpoints: profile management, credits.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.core.security import hash_password, verify_password
from app.core.deps import get_current_active_user

router = APIRouter()


# Request/Response schemas
class UpdateProfileRequest(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=255)


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=100)


class CreditBalanceResponse(BaseModel):
    credits: int
    pending_jobs: int


class ProfileResponse(BaseModel):
    id: str
    email: str
    name: str | None
    credits: int
    is_verified: bool
    created_at: str

    class Config:
        from_attributes = True


@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credits(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get user's credit balance and pending jobs count."""
    from app.models.research import ResearchJob

    pending_count = db.query(ResearchJob).filter(
        ResearchJob.user_id == current_user.id,
        ResearchJob.status.in_(["pending", "processing"])
    ).count()

    return CreditBalanceResponse(
        credits=current_user.credits,
        pending_jobs=pending_count
    )


@router.patch("/profile", response_model=ProfileResponse)
async def update_profile(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update user profile."""
    if request.name is not None:
        current_user.name = request.name

    db.commit()
    db.refresh(current_user)

    return ProfileResponse(
        id=current_user.id,
        email=current_user.email,
        name=current_user.name,
        credits=current_user.credits,
        is_verified=current_user.is_verified,
        created_at=current_user.created_at.isoformat()
    )


@router.post("/change-password")
async def change_password(
    request: ChangePasswordRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Change user's password."""
    # Verify current password
    if not verify_password(request.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )

    # Update password
    current_user.password_hash = hash_password(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}
