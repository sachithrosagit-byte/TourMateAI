"""Unit tests for the AI service layer (services/ai_service.py).

These exercise the mock implementations directly (the ``app`` fixture already
runs inside an app context with the 3 seeded attractions — see conftest.py:
Sigiriya/Heritage, Galle Fort/Historical, Mirissa Beach/Beach), plus the
``USE_MOCK_AI`` dispatch to the not-yet-built real modules.

The HTTP wrapper is covered separately in test_dashboard.py.
"""

from types import SimpleNamespace

import pytest

from app.extensions import db
from app.models import Attraction, User
from app.services import ai_service


def _make_user(uid="user1", interests=None):
    """Create a User with optional interest preferences and return it."""
    user = User(
        name=uid,
        email=f"{uid}@example.com",
        firebase_uid=uid,
        preferences={"interests": interests or []},
    )
    db.session.add(user)
    db.session.commit()
    return user


def _fake_image(filename="photo.jpg"):
    """Stand-in for a Werkzeug FileStorage; only ``.filename`` is ever read."""
    return SimpleNamespace(filename=filename)


# --- get_recommendations -----------------------------------------------------

def test_get_recommendations_shape(app):
    user = _make_user()
    recs = ai_service.get_recommendations(user.id, limit=10)

    assert isinstance(recs, list)
    assert len(recs) == 3  # all seeded attractions fit under the limit
    first = recs[0]
    # full attraction fields + the recommendation-contract fields
    assert {"id", "name", "category", "avg_rating", "score", "reason"} <= first.keys()
    assert 0 < first["score"] <= 0.99


def test_get_recommendations_interest_matches_come_first(app):
    user = _make_user(interests=["Beach"])
    recs = ai_service.get_recommendations(user.id, limit=10)

    assert recs[0]["category"] == "Beach"
    assert "Beach" in recs[0]["reason"]
    # interest match scores above the generic fillers, which follow it
    assert recs[0]["score"] > recs[1]["score"]
    assert all("Popular" in r["reason"] for r in recs[1:])


def test_get_recommendations_respects_limit(app):
    user = _make_user(interests=["Beach"])
    recs = ai_service.get_recommendations(user.id, limit=2)

    assert len(recs) == 2
    assert len({r["id"] for r in recs}) == 2  # no duplicates across match + fill


def test_get_recommendations_no_preferences_falls_back_to_popular(app):
    user = _make_user(interests=[])
    recs = ai_service.get_recommendations(user.id, limit=10)

    assert len(recs) == 3
    assert all("Popular" in r["reason"] for r in recs)


def test_get_recommendations_unknown_user_does_not_raise(app):
    # No such user id — should behave like "no preferences", not crash.
    recs = ai_service.get_recommendations(999999, limit=5)
    assert len(recs) == 3
    assert all("Popular" in r["reason"] for r in recs)


def test_get_recommendations_none_user_id(app):
    recs = ai_service.get_recommendations(None, limit=5)
    assert len(recs) == 3


# --- chatbot_reply -----------------------------------------------------------

def test_chatbot_reply_shape(app):
    out = ai_service.chatbot_reply(None, "hello there")
    assert set(out) == {"reply", "suggested_attractions"}
    assert isinstance(out["reply"], str) and out["reply"]
    assert isinstance(out["suggested_attractions"], list)


def test_chatbot_reply_beach_keyword(app):
    out = ai_service.chatbot_reply(None, "Where are the best beaches to swim?")
    assert "beach" in out["reply"].lower()
    # suggestions point at real Beach attractions
    assert out["suggested_attractions"]
    for aid in out["suggested_attractions"]:
        assert db.session.get(Attraction, aid).category == "Beach"


def test_chatbot_reply_weather_is_canned_with_no_suggestions(app):
    out = ai_service.chatbot_reply(None, "what's the weather like in July?")
    assert "forecast" in out["reply"].lower()
    assert out["suggested_attractions"] == []


def test_chatbot_reply_weather_takes_precedence_over_category(app):
    # "beach" + "weather" -> weather rule wins (checked first).
    out = ai_service.chatbot_reply(None, "how's the beach weather?")
    assert out["suggested_attractions"] == []
    assert "forecast" in out["reply"].lower()


def test_chatbot_reply_heritage_keyword(app):
    out = ai_service.chatbot_reply(None, "tell me about ancient ruins and history")
    assert out["suggested_attractions"]
    cats = {
        db.session.get(Attraction, aid).category
        for aid in out["suggested_attractions"]
    }
    assert cats <= {"Heritage", "Historical"}


def test_chatbot_reply_fallback_still_suggests(app):
    out = ai_service.chatbot_reply(None, "asdfqwer zzz")
    assert "TourMate" in out["reply"]
    assert out["suggested_attractions"]  # generic fallback offers popular picks


def test_chatbot_reply_empty_message_does_not_crash(app):
    out = ai_service.chatbot_reply(None, "")
    assert set(out) == {"reply", "suggested_attractions"}


# --- recognize_image ---------------------------------------------------------

def test_recognize_image_shape_and_match(app):
    res = ai_service.recognize_image(_fake_image())
    assert set(res) == {
        "identified_name",
        "confidence",
        "matched_attraction_id",
        "description",
    }
    assert 0.0 <= res["confidence"] <= 1.0

    # the mock always "matches" a real seeded attraction
    matched = db.session.get(Attraction, res["matched_attraction_id"])
    assert matched is not None
    assert res["identified_name"] == matched.name


def test_recognize_image_empty_catalogue(app):
    Attraction.query.delete()
    db.session.commit()

    res = ai_service.recognize_image(_fake_image())
    assert res["matched_attraction_id"] is None
    assert res["confidence"] == 0.0
    assert res["identified_name"] == "Unknown"


# --- USE_MOCK_AI dispatch -----------------------------------------------------

def test_real_branches_raise_until_wired_up(app):
    app.config["USE_MOCK_AI"] = False
    user = _make_user()

    with pytest.raises(NotImplementedError):
        ai_service.get_recommendations(user.id)
    with pytest.raises(NotImplementedError):
        ai_service.chatbot_reply(user.id, "hi")
    with pytest.raises(NotImplementedError):
        ai_service.recognize_image(_fake_image())
