"""Recommendations endpoint backing the Dashboard's "Recommended for you" section.

This route is a thin HTTP wrapper. All the actual logic — interest-filtered
picks today, the real recommendation engine later — lives behind
``services.ai_service.get_recommendations()``. Swapping the mock for the real
engine is a config flip (``USE_MOCK_AI``), not a change here.

The response mirrors ``POST /api/ai/recommend`` (docs/api-contract.md) — each
item carries ``score`` + ``reason`` alongside the full attraction fields the
cards need. ``"source"`` reports which implementation answered ("mock" vs "ai")
so the frontend / debugging can tell them apart.

Routes (registered under ``/api``):
  - ``GET /api/recommendations/mock``   auth: personalized attraction picks
"""

from flask import Blueprint, current_app, g, jsonify, request

from ..services.ai_service import get_recommendations
from .auth import require_auth
from .helpers import json_error

recommendations_bp = Blueprint("recommendations", __name__)

DEFAULT_LIMIT = 8
MAX_LIMIT = 24


@recommendations_bp.get("/recommendations")
@require_auth
def mock_recommendations():
    """Personalized attraction picks for the current user.

    Query params:
      - ``limit``  max items to return (default 8, capped at 24)

    Delegates to ``ai_service.get_recommendations`` (mock or real per
    ``USE_MOCK_AI``); this endpoint only parses/validates input and shapes the
    envelope. The route name keeps the ``/mock`` path for frontend compatibility.
    """
    raw_limit = request.args.get("limit", str(DEFAULT_LIMIT))
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return json_error("limit must be an integer.", 400)
    if limit < 1:
        return json_error("limit must be positive.", 400)
    limit = min(limit, MAX_LIMIT)

    recommendations = get_recommendations(g.current_user.id, limit=limit)

    source = "mock" if current_app.config.get("USE_MOCK_AI", True) else "ai"
    return jsonify({"recommendations": recommendations, "source": source})
