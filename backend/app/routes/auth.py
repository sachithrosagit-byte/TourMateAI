"""Authentication endpoints and the ``require_auth`` guard.

Flow: the React client signs in with Firebase (email/password) and sends the
Firebase ID token as ``Authorization: Bearer <token>``.

- ``POST /api/auth/verify`` validates that token, upserts the matching Users row
  (keyed on ``firebase_uid``), and returns it. The client calls this right after
  sign-in / sign-up to make sure a DB row exists for the Firebase account.
- ``GET  /api/auth/me`` returns the current user (demonstrates the guard).
- ``@require_auth`` protects any route: it verifies the bearer token and attaches
  the resolved User to ``flask.g`` as ``g.current_user`` (and ``g.firebase_uid``).
"""

from functools import wraps

from firebase_admin import auth as firebase_auth
from flask import Blueprint, g, jsonify, request

from ..extensions import db
from ..models import User
from ..services.firebase import verify_token

auth_bp = Blueprint("auth", __name__)


class _AuthError(Exception):
    """Internal: carries the HTTP status + JSON body for an auth failure.

    Uses the shared single-field ``{"error": <message>}`` shape so auth failures
    match every other endpoint's error contract (see routes/helpers.py).
    """

    def __init__(self, status, message):
        super().__init__(message)
        self.status = status
        self.payload = {"error": message}


def _extract_bearer_token():
    """Return the token from an ``Authorization: Bearer <token>`` header, or None."""
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        return None
    return header[len("Bearer ") :].strip() or None


def _decode_token(token):
    """Verify a token, translating library errors into ``_AuthError``s."""
    if not token:
        raise _AuthError(
            401, "Authorization header with a Bearer token is required."
        )
    try:
        return verify_token(token)
    except FileNotFoundError:
        raise _AuthError(
            503, "Firebase credentials are not configured on the server."
        )
    except firebase_auth.ExpiredIdTokenError:
        raise _AuthError(401, "Firebase ID token has expired; sign in again.")
    except (firebase_auth.RevokedIdTokenError,):
        raise _AuthError(401, "Firebase ID token has been revoked.")
    except (firebase_auth.InvalidIdTokenError, ValueError):
        raise _AuthError(401, "Invalid Firebase ID token.")


def _get_or_create_user(decoded):
    """Fetch the User for a Firebase uid, creating (or linking) on first sign-in."""
    uid = decoded["uid"]
    email = decoded.get("email")

    user = User.query.filter_by(firebase_uid=uid).first()
    if user:
        # Keep the email in sync if it changed in Firebase.
        if email and user.email != email:
            user.email = email
            db.session.commit()
        return user

    # A row with this email may already exist (e.g. pre-seeded) without a
    # firebase_uid — link it instead of violating the unique-email constraint.
    if email:
        existing = User.query.filter_by(email=email).first()
        if existing:
            existing.firebase_uid = uid
            db.session.commit()
            return existing

    name = decoded.get("name") or (email.split("@")[0] if email else "User")
    user = User(name=name, email=email, firebase_uid=uid)
    db.session.add(user)
    db.session.commit()
    return user


def _serialize_user(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "firebase_uid": user.firebase_uid,
        "preferences": user.preferences,
        # `role` is what the React navbar/admin gate keys on; `is_admin` is the
        # raw column for anything that prefers the boolean.
        "is_admin": bool(user.is_admin),
        "role": "admin" if user.is_admin else "user",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def require_auth(f):
    """Protect a route: verify the bearer token, attach ``g.current_user``.

    Usage::

        @some_bp.get("/private")
        @require_auth
        def private():
            return jsonify(user=g.current_user.email)
    """

    @wraps(f)
    def wrapper(*args, **kwargs):
        try:
            decoded = _decode_token(_extract_bearer_token())
        except _AuthError as exc:
            return jsonify(exc.payload), exc.status
        g.firebase_uid = decoded["uid"]
        g.current_user = _get_or_create_user(decoded)
        return f(*args, **kwargs)

    return wrapper


def require_admin(f):
    """Protect a route for admins only: ``require_auth`` + an ``is_admin`` check.

    Non-admin (but authenticated) callers get a 403 in the shared error shape.
    """

    @wraps(f)
    @require_auth
    def wrapper(*args, **kwargs):
        if not g.current_user.is_admin:
            return jsonify({"error": "Admin access required."}), 403
        return f(*args, **kwargs)

    return wrapper


@auth_bp.post("/verify")
def verify():
    """Verify a Firebase ID token and return (creating if needed) the DB user."""
    # Prefer the Authorization header (set by the Axios interceptor); fall back to
    # an ``id_token`` field in the JSON body for convenience / direct testing.
    token = _extract_bearer_token()
    if not token:
        token = (request.get_json(silent=True) or {}).get("id_token")
    try:
        decoded = _decode_token(token)
    except _AuthError as exc:
        return jsonify(exc.payload), exc.status

    user = _get_or_create_user(decoded)
    return jsonify({"user": _serialize_user(user)})


@auth_bp.get("/me")
@require_auth
def me():
    """Return the currently authenticated user."""
    return jsonify({"user": _serialize_user(g.current_user)})
