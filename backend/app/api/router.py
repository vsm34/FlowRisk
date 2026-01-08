from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from app.api import profile, runs, scenarios
from app.auth.deps import get_current_user
from app.core.config import settings
from app.models.user import User

router = APIRouter()

# Include sub-routers
router.include_router(profile.router, tags=["profile"])
router.include_router(scenarios.router, tags=["scenarios"])
router.include_router(runs.router, tags=["runs"])


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


@router.get("/v1/me")
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    """Get current authenticated user information."""
    return {
        "id": current_user.id,
        "firebase_uid": current_user.firebase_uid,
    }


@router.get("/v1/dev/whoami")
async def dev_whoami(current_user: Annotated[User, Depends(get_current_user)]):
    """
    DEV ONLY: Verify current user when using auth bypass.
    Only available when FLOWRISK_DEV_BYPASS_AUTH=true.
    """
    if not settings.flowrisk_dev_bypass_auth:
        raise HTTPException(
            status_code=404,
            detail="Dev endpoints only available when FLOWRISK_DEV_BYPASS_AUTH=true",
        )
    
    return {
        "message": "DEV BYPASS AUTH ACTIVE",
        "user_id": current_user.id,
        "firebase_uid": current_user.firebase_uid,
        "environment": settings.environment,
    }
