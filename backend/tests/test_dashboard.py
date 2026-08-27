"""Tests for the Dashboard's backing endpoints: mock recommendations +
the itineraries list."""

from app.extensions import db
from app.models import Attraction, Itinerary, ItineraryItem, User


def _set_preferences(app_ctx_user_uid, interests):
    """Create/lookup the test user for a uid and store interest prefs."""
    user = User.query.filter_by(firebase_uid=app_ctx_user_uid).first()
    if user is None:
        user = User(
            name=app_ctx_user_uid,
            email=f"{app_ctx_user_uid}@example.com",
            firebase_uid=app_ctx_user_uid,
        )
        db.session.add(user)
    user.preferences = {"interests": interests, "budget": None, "pace": None}
    db.session.commit()
    return user


# --- GET /api/recommendations/mock ------------------------------------------

def test_recommendations_require_auth(client):
    assert client.get("/api/recommendations/mock").status_code == 401


def test_recommendations_shape_and_source(client, app, auth_headers):
    r = client.get("/api/recommendations/mock", headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()
    assert body["source"] == "mock"
    assert len(body["recommendations"]) == 3  # all seeded attractions fit
    first = body["recommendations"][0]
    # attraction fields + the recommend-contract fields
    assert {"id", "name", "category", "avg_rating", "score", "reason"} <= first.keys()
    assert 0 < first["score"] <= 0.99


def test_recommendations_interest_matches_come_first(client, app, auth_headers):
    with app.app_context():
        _set_preferences("user1", ["Beach"])

    r = client.get("/api/recommendations/mock", headers=auth_headers)
    recs = r.get_json()["recommendations"]

    assert recs[0]["category"] == "Beach"
    assert "Beach" in recs[0]["reason"]
    # the rest are backfill with the generic reason
    assert all("Popular" in rec["reason"] for rec in recs[1:])
    # matched items outrank fillers
    assert recs[0]["score"] > recs[1]["score"]


def test_recommendations_no_preferences_falls_back_to_popular(client, app, auth_headers):
    r = client.get("/api/recommendations/mock", headers=auth_headers)
    recs = r.get_json()["recommendations"]
    assert len(recs) == 3
    assert all("Popular" in rec["reason"] for rec in recs)


def test_recommendations_limit_and_no_duplicates(client, app, auth_headers):
    with app.app_context():
        _set_preferences("user1", ["Beach"])

    r = client.get("/api/recommendations/mock?limit=2", headers=auth_headers)
    recs = r.get_json()["recommendations"]
    assert len(recs) == 2
    assert len({rec["id"] for rec in recs}) == 2


def test_recommendations_invalid_limit_returns_400(client, auth_headers):
    assert (
        client.get("/api/recommendations/mock?limit=abc", headers=auth_headers).status_code
        == 400
    )
    assert (
        client.get("/api/recommendations/mock?limit=0", headers=auth_headers).status_code
        == 400
    )


# --- GET /api/itineraries -----------------------------------------------------

def test_itineraries_require_auth(client):
    assert client.get("/api/itineraries").status_code == 401


def test_itineraries_empty_for_new_user(client, auth_headers):
    r = client.get("/api/itineraries", headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["itineraries"] == []


def test_itineraries_lists_own_plans_with_preview(client, app, auth_headers):
    with app.app_context():
        user = _set_preferences("user1", [])
        other = User(name="other", email="other@example.com", firebase_uid="other")
        db.session.add(other)
        db.session.flush()

        attractions = Attraction.query.order_by(Attraction.id).all()
        mine = Itinerary(user_id=user.id, title="South coast loop")
        theirs = Itinerary(user_id=other.id, title="Not my trip")
        db.session.add_all([mine, theirs])
        db.session.flush()
        db.session.add_all(
            [
                ItineraryItem(
                    itinerary_id=mine.id,
                    attraction_id=a.id,
                    day_number=1,
                    order_index=i,
                )
                for i, a in enumerate(attractions)
            ]
        )
        db.session.commit()

    r = client.get("/api/itineraries", headers=auth_headers)
    body = r.get_json()
    assert len(body["itineraries"]) == 1  # never another user's plans
    plan = body["itineraries"][0]
    assert plan["title"] == "South coast loop"
    assert plan["item_count"] == 3
    assert len(plan["preview_stops"]) == 3
