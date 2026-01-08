import logging
import os
from typing import Optional

import firebase_admin
from firebase_admin import auth, credentials

logger = logging.getLogger(__name__)

# Module-level flag to ensure Firebase is initialized only once
_firebase_initialized = False


def init_firebase() -> None:
    """
    Initialize Firebase Admin SDK exactly once.

    Credential strategy:
      1) FIREBASE_CREDENTIALS_PATH (recommended) -> credentials.Certificate(path)
      2) GOOGLE_APPLICATION_CREDENTIALS -> credentials.Certificate(path) or ApplicationDefault()
         (we attempt Certificate first to be explicit)
      3) If neither is set -> raise RuntimeError (misconfigured environment)

    Notes:
      - We do NOT initialize without credentials (unsafe / confusing).
      - If you want to run locally without Firebase, use the dev bypass in deps.py.
    """
    global _firebase_initialized

    if _firebase_initialized:
        return

    if firebase_admin._apps:
        # In case something else initialized it
        _firebase_initialized = True
        return

    creds_path = os.getenv("FIREBASE_CREDENTIALS_PATH")
    gac_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    try:
        if creds_path:
            logger.info("Initializing Firebase Admin using FIREBASE_CREDENTIALS_PATH")
            cred = credentials.Certificate(creds_path)
            firebase_admin.initialize_app(cred)
        elif gac_path:
            # Prefer explicit certificate if a file path is provided
            logger.info("Initializing Firebase Admin using GOOGLE_APPLICATION_CREDENTIALS")
            try:
                cred = credentials.Certificate(gac_path)
            except Exception:
                # Some environments use ADC sources that aren't a JSON service account file
                cred = credentials.ApplicationDefault()
            firebase_admin.initialize_app(cred)
        else:
            raise RuntimeError(
                "Firebase Admin credentials not configured. "
                "Set FIREBASE_CREDENTIALS_PATH (recommended) or GOOGLE_APPLICATION_CREDENTIALS."
            )

        _firebase_initialized = True

    except Exception as e:
        logger.exception("Failed to initialize Firebase Admin SDK: %s", e)
        raise


def verify_token(id_token: str) -> Optional[dict]:
    """
    Verify Firebase ID token and return decoded token.

    Args:
        id_token: Firebase ID token from Authorization header

    Returns:
        Decoded token dict with 'uid' and other claims, or None if invalid/expired.
        Raises RuntimeError if Firebase Admin is misconfigured and cannot initialize.
    """
    init_firebase()

    try:
        decoded_token = auth.verify_id_token(id_token)
        return decoded_token
    except Exception:
        # Invalid/expired token, bad signature, etc.
        return None
