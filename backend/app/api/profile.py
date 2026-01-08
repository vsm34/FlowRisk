from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth.deps import get_current_user
from app.db.session import get_db
from app.models.debt import Debt
from app.models.financial_profile import FinancialProfile
from app.models.user import User
from app.schemas.debt import DebtCreateRequest, DebtResponse
from app.schemas.profile import ProfileResponse, ProfileUpsertRequest

router = APIRouter()


@router.get("/v1/profile", response_model=ProfileResponse)
async def get_profile(
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Get current user's financial profile."""
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == current_user.id)
        .first()
    )
    
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    
    return profile


@router.post("/v1/profile", response_model=ProfileResponse)
async def upsert_profile(
    request: ProfileUpsertRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Create or update current user's financial profile."""
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == current_user.id)
        .first()
    )
    
    if profile:
        # Update existing profile
        for field, value in request.model_dump().items():
            setattr(profile, field, value)
    else:
        # Create new profile
        profile = FinancialProfile(
            user_id=current_user.id,
            **request.model_dump(),
        )
        db.add(profile)
    
    db.commit()
    db.refresh(profile)
    return profile


@router.post("/v1/profile/debts", response_model=DebtResponse)
async def create_debt(
    request: DebtCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Add a debt to current user's financial profile."""
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.user_id == current_user.id)
        .first()
    )
    
    if not profile:
        raise HTTPException(
            status_code=404,
            detail="Profile not found. Create a profile first.",
        )
    
    debt = Debt(
        profile_id=profile.id,
        **request.model_dump(),
    )
    db.add(debt)
    db.commit()
    db.refresh(debt)
    return debt


@router.delete("/v1/profile/debts/{debt_id}", status_code=204)
async def delete_debt(
    debt_id: int,
    current_user: Annotated[User, Depends(get_current_user)],
    db: Annotated[Session, Depends(get_db)],
):
    """Delete a debt (only if it belongs to current user)."""
    debt = db.query(Debt).filter(Debt.id == debt_id).first()
    
    if not debt:
        raise HTTPException(status_code=404, detail="Debt not found")
    
    # Verify ownership through profile
    profile = (
        db.query(FinancialProfile)
        .filter(FinancialProfile.id == debt.profile_id)
        .first()
    )
    
    if not profile or profile.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Forbidden")
    
    db.delete(debt)
    db.commit()
    return None
