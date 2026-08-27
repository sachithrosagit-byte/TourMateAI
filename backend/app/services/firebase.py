"""Firebase Admin SDK integration.

Initialises the Admin SDK once (lazily, thread-safe) from the service-account JSON
pointed to by the ``FIREBASE_CREDENTIALS`` env var, and exposes a thin wrapper to
verify Firebase ID tokens minted by the client.

The React client authenticates users with the Firebase JS SDK (email/password) and
sends the resulting ID token as ``Authorization: Bearer <token>``. The backend only
ever *verifies* tokens here — it never sees or stores raw passwords.
"""

import os
import threading
from pathlib import Path

import firebase_admin
from firebase_admin import auth as firebase_auth
from firebase_admin import credentials

# backend/app/services/firebase.py -> parents[2] == backend/
_BACKEND_DIR = Path(__file__).resolve().parents[2]

_init_lock = threading.Lock()
_initialised = False


def _resolve_credentials_path():
    """Return the absolute path to the service-account JSON.

    ``FIREBASE_CREDENTIALS`` may be absolute or relative; relative paths are
    resolved against the backend/ directory (the process working dir convention).
    """
    raw = os.environ.get("FIREBASE_CREDENTIALS", "serviceAccountKey.json")
    path = Path(raw)
    if not path.is_absolute():
        path = _BACKEND_DIR / path
    return path


def init_firebase():
    """Initialise the default Firebase app exactly once (idempotent, thread-safe).

    Raises FileNotFoundError with actionable guidance if the credentials file is
    missing, so callers can surface a clean 503 rather than a raw stack trace.
    """
    global _initialised
    if _initialised or firebase_admin._apps:
        _initialised = True
        return

    with _init_lock:
        if _initialised or firebase_admin._apps:
            _initialised = True
            return

        cred_path = _resolve_credentials_path()
        if not cred_path.exists():
            raise FileNotFoundError(
                f"Firebase service-account file not found at '{cred_path}'. "
                "Download it from the Firebase console (Project settings > Service "
                "accounts) and point FIREBASE_CREDENTIALS at it in your .env."
            )

        cred = credentials.Certificate(str(cred_path))
        firebase_admin.initialize_app(cred)
        _initialised = True


def verify_token(id_token):
    """Verify a Firebase ID token and return its decoded claims (dict with ``uid``).

    Lazily initialises the Admin SDK on first use. Propagates
    ``firebase_admin.auth`` errors (Expired/Invalid/Revoked) to the caller and
    ``FileNotFoundError`` if the server has no credentials configured.
    """
    init_firebase()
    return firebase_auth.verify_id_token(id_token)
