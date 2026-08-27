"""AI service layer — the single seam between the web app and the AI features.

Three AI capabilities are being built **in parallel** by the AI developer as
self-contained modules under ``backend/app/ai/`` (recommender, chatbot, vision).
They do not exist yet. So that the rest of the app — routes, and the React UI on
top of them — can be built, demoed and tested *today*, this module ships
**realistic mock implementations** behind the exact function signatures the real
modules must satisfy.

Every function here is a dispatcher:

    def feature(...):
        if _use_mock_ai():
            return _mock_feature(...)     # what runs now
        return _real_feature(...)         # teammate's real module (stubbed TODO)

Flip ``USE_MOCK_AI`` in ``.env`` from ``True`` to ``False`` once the real
modules land and the ``_real_*`` stubs are wired up — no caller changes needed.
The mocks live under ``USE_MOCK_AI=True`` (the default) so nothing breaks before
that swap.

--------------------------------------------------------------------------------
CONTRACTS (the real implementations MUST match these signatures + return shapes)
--------------------------------------------------------------------------------

1. get_recommendations(user_id: int, limit: int = 10) -> list[dict]
   Personalized attraction picks for a user. Each dict is a full serialized
   attraction (see routes/attractions._serialize_attraction) PLUS:
       "score":  float in (0, 1]   — relevance/confidence, higher is better
       "reason": str               — short human-readable justification
   Ordered best-first. Length <= limit. Never raises for an unknown/None user;
   falls back to popular picks.

2. chatbot_reply(user_id: int, message: str,
                 conversation_history: list[dict] | None = None)
       -> {"reply": str, "suggested_attractions": list[int]}
   One conversational turn. ``conversation_history`` is prior turns (oldest
   first), each e.g. {"role": "user"|"assistant", "content": str}; may be None.
   ``suggested_attractions`` is Attraction ids the reply refers to (may be []).

3. recognize_image(image_file) -> {
           "identified_name": str,
           "confidence": float,                    # 0.0 .. 1.0
           "matched_attraction_id": int | None,    # None when unmatched
           "description": str,
       }
   ``image_file`` is a Werkzeug FileStorage (request.files["image"]). The real
   model runs inference; below its confidence threshold it should return a low
   ``confidence`` with ``matched_attraction_id = None``.

--------------------------------------------------------------------------------
These map onto the public HTTP contracts in ``docs/api-contract.md`` (POST
/api/ai/recommend, /chat, /identify). Keep field names in sync with that doc.
"""

import random

from flask import current_app

from ..extensions import db
from ..models import Attraction, User
# Reused so mock recommendations carry the *identical* attraction shape the rest
# of the API already returns — keeps the frontend contract single-sourced.
from ..routes.attractions import _serialize_attraction


def _use_mock_ai():
    """Whether to route to the mock stand-ins (True) or the real modules (False).

    Driven by ``USE_MOCK_AI`` (see config.py / .env). Defaults to True so the app
    keeps working before the real AI modules exist.
    """
    return current_app.config.get("USE_MOCK_AI", True)


# =============================================================================
# 1. RECOMMENDATIONS
# =============================================================================

def get_recommendations(user_id, limit=10):
    """Personalized attraction recommendations for a user. See module contract §1."""
    if _use_mock_ai():
        return _mock_get_recommendations(user_id, limit)
    return _real_get_recommendations(user_id, limit)


# --- mock ---------------------------------------------------------------------

# Recommendation-scoring constants (mock heuristic only).
_SCORE_INTEREST_BOOST = 0.12
_SCORE_UNRATED_DEFAULT = 3.0   # treat unrated attractions as middling, not zero
_SCORE_CAP = 0.99


def _mock_score(attraction, matched_interest):
    """Deterministic pseudo-score in (0, 1): rating-driven, interest-boosted."""
    rating = attraction.avg_rating or _SCORE_UNRATED_DEFAULT
    base = 0.5 + (rating / 5.0) * 0.35  # 0.5 .. 0.85
    if matched_interest:
        base += _SCORE_INTEREST_BOOST
    return round(min(base, _SCORE_CAP), 2)


def _mock_serialize_recommendation(attraction, matched_interest):
    """Full attraction dict + ``score``/``reason`` (the recommendation shape)."""
    data = _serialize_attraction(attraction)
    data["score"] = _mock_score(attraction, matched_interest)
    data["reason"] = (
        f"Matches your interest in {matched_interest}"
        if matched_interest
        else "Popular with travelers across Sri Lanka"
    )
    return data


def _mock_get_recommendations(user_id, limit):
    """Interest-filtered attraction picks (mock recommendation engine).

    Mirrors the honest heuristic the Dashboard was first built against: rank
    attractions in the user's interest categories by rating, then top up with
    the highest-rated attractions from other categories. Works (as "popular
    picks") for an unknown user or one with no stored preferences.

    User.preferences.interests values equal Attraction.category values by design
    (see routes/users.py), which is what makes the ``category IN interests``
    filter meaningful.
    """
    limit = max(1, int(limit))

    user = db.session.get(User, user_id) if user_id is not None else None
    prefs = (user.preferences if user else None) or {}
    interests = [i for i in (prefs.get("interests") or []) if isinstance(i, str)]

    by_rating = (Attraction.avg_rating.desc(), Attraction.name.asc())

    matched = []
    if interests:
        matched = (
            Attraction.query.filter(Attraction.category.in_(interests))
            .order_by(*by_rating)
            .limit(limit)
            .all()
        )

    recommendations = [
        _mock_serialize_recommendation(a, a.category) for a in matched
    ]

    if len(matched) < limit:
        fill_query = Attraction.query
        if matched:
            fill_query = fill_query.filter(
                Attraction.id.notin_([a.id for a in matched])
            )
        fillers = fill_query.order_by(*by_rating).limit(limit - len(matched)).all()
        recommendations.extend(
            _mock_serialize_recommendation(a, None) for a in fillers
        )

    return recommendations


# --- real (teammate's recommendation engine — not built yet) ------------------

def _real_get_recommendations(user_id, limit):
    from ..ai.recommender import recommend
    return recommend(user_id=user_id, limit=limit)


# =============================================================================
# 2. CHATBOT
# =============================================================================

def chatbot_reply(user_id, message, conversation_history=None):
    """One chatbot turn. See module contract §2."""
    if _use_mock_ai():
        return _mock_chatbot_reply(user_id, message, conversation_history)
    return _real_chatbot_reply(user_id, message, conversation_history)


# --- mock ---------------------------------------------------------------------

# Rule table: (trigger keywords, attraction categories to suggest, reply text).
# First matching rule wins; ``categories`` drives ``suggested_attractions``.
# Ordered most-specific-intent first.
_CHAT_RULES = [
    (
        ("beach", "coast", "sea", "swim", "surf", "snorkel", "whale"),
        ("Beach",),
        "Sri Lanka has gorgeous beaches! The south coast — Mirissa and Unawatuna "
        "near Galle — is great for swimming and whale watching, while Trincomalee "
        "on the east coast has calm bays. Here are a few to start with.",
    ),
    (
        ("wildlife", "safari", "leopard", "elephant", "animal", "bird"),
        ("Wildlife",),
        "For wildlife, Yala National Park has one of the world's highest leopard "
        "densities, and Pinnawala is famous for its elephants. A dawn safari gives "
        "you the best sightings.",
    ),
    (
        ("hike", "hiking", "trek", "climb", "mountain", "trail", "summit"),
        ("Hiking", "Nature"),
        "If you like hiking, Adam's Peak (Sri Pada) is a classic pre-dawn "
        "pilgrimage climb, and Horton Plains leads to the dramatic World's End "
        "escarpment. Start early to beat the mist and heat.",
    ),
    (
        ("temple", "religious", "buddhist", "worship", "sacred", "pilgrim"),
        ("Religious",),
        "For temples, the Temple of the Sacred Tooth Relic in Kandy is the most "
        "revered Buddhist site in the country. Dress modestly (shoulders and knees "
        "covered) when you visit.",
    ),
    (
        ("history", "historical", "heritage", "ancient", "ruins", "fort", "unesco"),
        ("Heritage", "Historical"),
        "History buffs are spoiled here: Sigiriya rock fortress, the ancient "
        "cities of Anuradhapura and Polonnaruwa, and the colonial ramparts of "
        "Galle Fort are all UNESCO-listed highlights.",
    ),
    (
        ("tea", "hill", "highland", "cool", "ella", "nuwara", "scenic", "train"),
        ("Hill Country", "Scenic"),
        "The hill country is beautiful and cool — Nuwara Eliya's tea estates and "
        "Ella's Nine Arch Bridge are highlights, and the Kandy-to-Ella train is one "
        "of the world's most scenic rides.",
    ),
]

# "Weather" gets a canned, honest reply — the mock has no live forecast feed.
_CHAT_WEATHER_KEYWORDS = ("weather", "rain", "forecast", "temperature", "monsoon", "season")
_CHAT_WEATHER_REPLY = (
    "I can't pull a live forecast in this demo, but as a rule of thumb: Sri "
    "Lanka's south and west coasts are driest from December to March, while the "
    "east coast (Trincomalee, Arugam Bay) is best from May to September. The hill "
    "country stays cool and can be misty year-round — bring a light jacket."
)

_CHAT_FALLBACK_REPLY = (
    "I'm your TourMate assistant for exploring Sri Lanka! Ask me about beaches, "
    "wildlife safaris, ancient heritage sites, hiking trails, temples, the hill "
    "country, or the best time to visit — and I'll point you to some great spots."
)


def _top_attraction_ids(categories=None, limit=3):
    """Ids of the highest-rated attractions, optionally within ``categories``."""
    query = Attraction.query
    if categories:
        query = query.filter(Attraction.category.in_(categories))
    rows = (
        query.order_by(Attraction.avg_rating.desc(), Attraction.name.asc())
        .limit(limit)
        .all()
    )
    return [a.id for a in rows]


def _mock_chatbot_reply(user_id, message, conversation_history):
    """Rule-based keyword matching — enough to demo the full chat UI flow.

    Deliberately shallow: no retrieval, no LLM, no real understanding of
    ``conversation_history`` (accepted for signature parity only). Good enough to
    exercise the chat screen end-to-end; the real RAG chatbot replaces this.
    """
    text = (message or "").lower()

    # Weather is handled before the category rules so "beach weather" -> weather.
    if any(kw in text for kw in _CHAT_WEATHER_KEYWORDS):
        return {"reply": _CHAT_WEATHER_REPLY, "suggested_attractions": []}

    for keywords, categories, reply in _CHAT_RULES:
        if any(kw in text for kw in keywords):
            return {
                "reply": reply,
                "suggested_attractions": _top_attraction_ids(categories),
            }

    # Friendly generic fallback — still offer a couple of popular spots.
    return {
        "reply": _CHAT_FALLBACK_REPLY,
        "suggested_attractions": _top_attraction_ids(),
    }


# --- real (teammate's RAG chatbot — not built yet) ----------------------------

def _real_chatbot_reply(user_id, message, conversation_history):
    from ..ai.chatbot.agent import answer
    return answer(user_id=user_id, message=message, conversation_history=conversation_history)


# =============================================================================
# 3. IMAGE / LANDMARK RECOGNITION
# =============================================================================

def recognize_image(image_file):
    """Identify a landmark from an uploaded image. See module contract §3."""
    if _use_mock_ai():
        return _mock_recognize_image(image_file)
    return _real_recognize_image(image_file)


# --- mock ---------------------------------------------------------------------

def _mock_recognize_image(image_file):
    """MOCK landmark recognition — DOES NOT LOOK AT THE IMAGE AT ALL.

    !!! MOCK — REPLACE WITH THE REAL VISION MODEL !!!
    There is no image analysis here. We simply pick a RANDOM attraction from the
    database and return it as if the model had recognized it, with a plausible
    made-up confidence. This exists only so the upload -> result UI flow can be
    built and demoed. The ``image_file`` is accepted (and could be logged) but
    its pixels are never inspected.
    """
    # Touch the argument so the signature is honest and a totally-empty upload is
    # still distinguishable, but note: filename/content is NOT used to identify.
    _ = getattr(image_file, "filename", None)

    attraction = Attraction.query.order_by(Attraction.id).all()
    if not attraction:
        # Empty catalogue: nothing to "recognize".
        return {
            "identified_name": "Unknown",
            "confidence": 0.0,
            "matched_attraction_id": None,
            "description": "No attractions in the database to match against.",
        }

    picked = random.choice(attraction)
    # Realistic-looking high-ish confidence so the "recognized" UI branch shows.
    confidence = round(random.uniform(0.78, 0.97), 2)

    return {
        "identified_name": picked.name,
        "confidence": confidence,
        "matched_attraction_id": picked.id,
        "description": picked.description
        or f"{picked.name} is a notable attraction in Sri Lanka.",
    }


def _real_recognize_image(image_file):
    from ..ai.vision.classifier import identify
    return identify(image_file)
