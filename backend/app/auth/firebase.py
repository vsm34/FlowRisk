from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials

# Module-level flag to ensure Firebase is initialized only once
_firebase_initialized = False


def init_firebase() -> None:
    """Initialize Firebase Admin SDK."""
    global _firebase_initialized
    
    if _firebase_initialized:
        return
    
    try:
        # Use default credentials for MVP
        # In production, set GOOGLE_APPLICATION_CREDENTIALS environment variable
        cred = credentials.ApplicationDefault()
        firebase_admin.initialize_app(cred)
        _firebase_initialized = True
    except Exception:
        # If default credentials fail, initialize without credentials for development
        firebase_admin.initialize_app()
        _firebase_initialized = True


def verify_token(id_token: str) -> Optional[dict]:
    """
    Verify Firebase ID token and return decoded token.
    
    Args:
        id_token: Firebase ID token from Authorization header
        
    Returns:
        Decoded token dict with 'uid' and other claims, or None if invalid
    """
    init_firebase()
    
    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception:
        return None
