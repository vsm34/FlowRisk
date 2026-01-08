import logging
from typing import Annotated, Optional

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from app.auth.firebase import verify_token
from app.core.config import settings
from app.db.session import get_db
from app.models.user import User

logger = logging.getLogger(__name__)

DEV_BYPASS_UID = "dev-bypass"


def get_current_user(
    db: Annotated[Session, Depends(get_db)],
    authorization: Annotated[Optional[str], Header()] = None,
) -> User:
    """
    Get current authenticated user from Firebase token.
    Auto-provisions user in database if not exists.
    
    DEV MODE: If FLOWRISK_DEV_BYPASS_AUTH=true and environment != production,
    bypasses Firebase auth and returns/creates a dev user.
    
    Args:
        db: Database session
        authorization: Authorization header with Bearer token
        
    Returns:
        User object
        
    Raises:
        HTTPException: 401 if token is missing or invalid
    """
    # DEV BYPASS: Only if explicitly enabled AND not in production
    if (
        settings.flowrisk_dev_bypass_auth
        and settings.environment.lower() != "production"
    ):
        logger.warning("DEV BYPASS AUTH ENABLED - using dev user")
        
        # Find or create dev bypass user
        user = db.query(User).filter(User.firebase_uid == DEV_BYPASS_UID).first()
        
        if not user:
            logger.info(f"Creating dev bypass user with uid={DEV_BYPASS_UID}")
            user = User(firebase_uid=DEV_BYPASS_UID)
            db.add(user)
            db.commit()
            db.refresh(user)
        
        return user
    
    # Normal Firebase authentication
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")
    
    # Expect "Bearer <token>"
    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Missing Authorization Bearer token")
    
    id_token = parts[1]
    
    # Verify token with Firebase
    decoded_token = verify_token(id_token)
    if not decoded_token:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    
    firebase_uid = decoded_token.get("uid")
    if not firebase_uid:
        raise HTTPException(status_code=401, detail="Token missing uid claim")
    
    # Find or create user
    user = db.query(User).filter(User.firebase_uid == firebase_uid).first()
    
    if not user:
        # Auto-provision user
        user = User(firebase_uid=firebase_uid)
        db.add(user)
        db.commit()
        db.refresh(user)
    
    return user
