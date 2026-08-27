"""Interaction logging endpoint — the recommender's training signal.

Every time an authenticated user views / likes / visits an attraction the
frontend posts one event here. These rows are the implicit-feedback dataset the
content-based recommender (``app/ai/recommender``) will later consume, so the
payload is kept deliberately small and stable:

    POST /api/interactions
    Authorization: Bearer <firebase-id-token>
    {
      "attraction_id": 7,          # int, required — must reference an Attraction
      "interaction_type": "view"   # str, required — one of: view | like | visit
    }

The user is taken from the auth token (never the body) so a client cannot log
events on another user's behalf. Response (201):

    {
      "interaction": {
        "id": 1,
        "user_id": 3,
        "attraction_id": 7,
        "interaction_type": "view",
        "created_at": "2026-07-05T10:15:00"
      }
    }
"""

from flask import Blueprint, g, jsonify, request

from ..extensions import db
from ..models import Attraction, Interaction, InteractionType
from .auth import require_auth
from .helpers import json_error

interactions_bp = Blueprint("interactions", __name__)

VALID_TYPES = tuple(t.value for t in InteractionType)  # ("view", "like", "visit")


def _serialize_interaction(interaction):
    return {
        "id": interaction.id,
        "user_id": interaction.user_id,
        "attraction_id": interaction.attraction_id,
        "interaction_type": (
            interaction.interaction_type.value
            if interaction.interaction_type
            else None
        ),
        "created_at": (
            interaction.created_at.isoformat() if interaction.created_at else None
        ),
    }


@interactions_bp.post("/interactions")
@require_auth
def log_interaction():
    """Record one user↔attraction interaction event (see module docstring)."""
    body = request.get_json(silent=True) or {}
    attraction_id = body.get("attraction_id")
    interaction_type = body.get("interaction_type")

    # bool is a subclass of int — reject True/False sent as an id.
    if not isinstance(attraction_id, int) or isinstance(attraction_id, bool):
        return json_error("attraction_id is required and must be an integer.", 400)

    if not isinstance(interaction_type, str) or interaction_type not in VALID_TYPES:
        return json_error(
            f"interaction_type is required and must be one of: "
            f"{', '.join(VALID_TYPES)}.",
            400,
        )

    if db.session.get(Attraction, attraction_id) is None:
        return json_error("Attraction not found.", 404)

    interaction = Interaction(
        user_id=g.current_user.id,
        attraction_id=attraction_id,
        interaction_type=InteractionType(interaction_type),
    )
    db.session.add(interaction)
    db.session.commit()

    return jsonify({"interaction": _serialize_interaction(interaction)}), 201
