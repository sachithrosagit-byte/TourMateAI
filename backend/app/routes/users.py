"""User profile endpoints — the logged-in user's own account + travel prefs.

These back the React Profile page. Everything here operates on *the current
user* (resolved from the Firebase token by ``require_auth``) — never a user id
from the request — so a client can only ever read/write its own profile.

Routes (registered under ``/api/users``):
  - ``GET  /api/users/me``            fetch the current user's profile
  - ``PUT  /api/users/me``            update name + travel preferences
  - ``GET  /api/users/me/feedback``   the ratings/reviews this user has left

Preferences shape
-----------------
``User.preferences`` is a small, stable JSON object that the teammate's
recommendation engine reads (see docs/api-contract.md → POST /api/ai/recommend).
Keep it flat and boring::

    {
      "interests": ["Beach", "Wildlife"],   # subset of INTEREST_OPTIONS below;
                                             # each value equals an Attraction.category
                                             # so the recommender can join directly
      "budget": "medium",                    # one of BUDGET_OPTIONS  (low|medium|high)
      "pace": "moderate"                     # one of PACE_OPTIONS (relaxed|moderate|packed)
    }

Any of the three keys may be absent / empty while the user is still filling in
their profile; the recommender must treat missing prefs as "no constraint".
"""

from flask import Blueprint, g, jsonify, request

from ..extensions import db
from ..models import Attraction, Feedback
from .auth import require_auth
from .helpers import json_error

users_bp = Blueprint("users", __name__)

# Allowed preference values. INTEREST_OPTIONS intentionally mirrors the set of
# ``Attraction.category`` values (see app/seed.py) so a user's interests map
# straight onto attraction categories for the recommender. Keep it in sync if
# the catalogue's categories change.
INTEREST_OPTIONS = (
    "Heritage",
    "Religious",
    "Historical",
    "Scenic",
    "Wildlife",
    "Hiking",
    "Hill Country",
    "Beach",
    "Nature",
)
BUDGET_OPTIONS = ("low", "medium", "high")
PACE_OPTIONS = ("relaxed", "moderate", "packed")

NAME_MAX_LEN = 120


def _serialize_user(user):
    """Shape a User row for JSON (matches routes/auth.py::_serialize_user)."""
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "firebase_uid": user.firebase_uid,
        "preferences": user.preferences,
        "is_admin": bool(user.is_admin),
        "role": "admin" if user.is_admin else "user",
        "created_at": user.created_at.isoformat() if user.created_at else None,
    }


def _serialize_feedback(feedback):
    """Shape a Feedback row + its attraction for the profile's review list."""
    attraction = feedback.attraction
    return {
        "id": feedback.id,
        "attraction_id": feedback.attraction_id,
        "attraction_name": attraction.name if attraction else None,
        "attraction_category": attraction.category if attraction else None,
        "rating": feedback.rating,
        "comment": feedback.comment,
        "created_at": (
            feedback.created_at.isoformat() if feedback.created_at else None
        ),
    }


def _validate_preferences(raw):
    """Validate + normalise an incoming preferences object.

    Returns ``(prefs_dict, error)``. On success ``error`` is None and
    ``prefs_dict`` is a clean ``{interests, budget, pace}`` object safe to store.
    On failure ``prefs_dict`` is None and ``error`` is a Flask response tuple.
    Absent keys are stored as ``[]`` / ``None`` so the shape is always complete.
    """
    if not isinstance(raw, dict):
        return None, json_error("preferences must be an object.", 400)

    # interests: optional list of known category strings, de-duplicated.
    interests_in = raw.get("interests", [])
    if interests_in is None:
        interests_in = []
    if not isinstance(interests_in, list):
        return None, json_error("preferences.interests must be a list.", 400)

    interests = []
    for item in interests_in:
        if item not in INTEREST_OPTIONS:
            return None, json_error(
                "preferences.interests may only contain: "
                f"{', '.join(INTEREST_OPTIONS)}.",
                400,
            )
        if item not in interests:  # preserve order, drop duplicates
            interests.append(item)

    # budget: optional single choice (or null/empty for "not set").
    budget = raw.get("budget") or None
    if budget is not None and budget not in BUDGET_OPTIONS:
        return None, json_error(
            f"preferences.budget must be one of: {', '.join(BUDGET_OPTIONS)}.",
            400,
        )

    # pace: optional single choice (or null/empty for "not set").
    pace = raw.get("pace") or None
    if pace is not None and pace not in PACE_OPTIONS:
        return None, json_error(
            f"preferences.pace must be one of: {', '.join(PACE_OPTIONS)}.", 400
        )

    return {"interests": interests, "budget": budget, "pace": pace}, None


@users_bp.get("/me")
@require_auth
def get_me():
    """Return the current user's profile (account fields + preferences)."""
    return jsonify({"user": _serialize_user(g.current_user)})


@users_bp.put("/me")
@require_auth
def update_me():
    """Update the current user's ``name`` and/or ``preferences``.

    Body (all fields optional — omit one to leave it unchanged)::

        { "name": "Ada Lovelace",
          "preferences": { "interests": [...], "budget": "medium", "pace": "moderate" } }

    Email is intentionally NOT editable here — it is owned by Firebase auth and
    kept in sync on sign-in (see routes/auth.py).
    """
    user = g.current_user
    body = request.get_json(silent=True) or {}

    if "name" in body:
        name = body.get("name")
        if not isinstance(name, str):
            return json_error("name must be a string.", 400)
        name = name.strip()
        if not name:
            return json_error("name cannot be empty.", 400)
        if len(name) > NAME_MAX_LEN:
            return json_error(
                f"name must be at most {NAME_MAX_LEN} characters.", 400
            )
        user.name = name

    if "preferences" in body:
        prefs, error = _validate_preferences(body.get("preferences") or {})
        if error:
            return error
        user.preferences = prefs

    db.session.commit()
    return jsonify({"user": _serialize_user(user)})


@users_bp.get("/me/feedback")
@require_auth
def my_feedback():
    """Return every rating/review the current user has left, newest first.

    Each item carries its attraction's name + category so the Profile page can
    render the history without a second round-trip per review.
    """
    rows = (
        Feedback.query.filter_by(user_id=g.current_user.id)
        .join(Attraction, Feedback.attraction_id == Attraction.id)
        .order_by(Feedback.created_at.desc())
        .all()
    )
    return jsonify({"feedback": [_serialize_feedback(f) for f in rows]})
