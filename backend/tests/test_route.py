"""Tests for the itinerary day-route endpoint + directions service caching.

The Google Routes API HTTP call is stubbed at ``services.directions._post_json``
so no network (or real API key) is needed. Itineraries/items are set up through
the real API using the fake-auth headers from conftest.
"""

import pytest

import app.services.directions as directions_service
from app.extensions import db
from app.models import Attraction

# --- Canned Routes API payloads ----------------------------------------------

# Three stops -> two legs. Totals intentionally differ from the leg sums a
# little (as real responses can) to prove we prefer the route-level figures.
_THREE_STOP_ROUTE = {
    "routes": [
        {
            "distanceMeters": 154000,
            "duration": "12600s",
            "legs": [
                {"distanceMeters": 90000, "duration": "7200s"},
                {"distanceMeters": 64000, "duration": "5400s"},
            ],
        }
    ]
}

# Four stops, optimized: Google says visiting intermediates in order [1, 0]
# (i.e. swap the two middle stops) is faster.
_OPTIMIZED_ROUTE = {
    "routes": [
        {
            "distanceMeters": 120000,
            "duration": "10800s",
            "legs": [
                {"distanceMeters": 40000, "duration": "3600s"},
                {"distanceMeters": 40000, "duration": "3600s"},
                {"distanceMeters": 40000, "duration": "3600s"},
            ],
            "optimizedIntermediateWaypointIndex": [1, 0],
        }
    ]
}


def _stub_post(monkeypatch, payload, calls=None):
    """Route _post_json to canned data; optionally record request bodies."""
    def fake(body, headers):
        if calls is not None:
            calls.append(body)
        return payload

    monkeypatch.setattr(directions_service, "_post_json", fake)


@pytest.fixture(autouse=True)
def _fresh_cache_and_key(app):
    """Isolate the module cache and give the app a (fake) key for each test."""
    directions_service.reset_cache()
    app.config["GOOGLE_MAPS_API_KEY"] = "test-key"
    yield
    directions_service.reset_cache()


def _make_trip(client, auth_headers, attraction_ids=(1, 2, 3), day=1):
    """Create a trip with the given attractions on one day; returns (trip_id, item_ids)."""
    r = client.post("/api/itineraries", json={"title": "Route test"}, headers=auth_headers)
    trip_id = r.get_json()["itinerary"]["id"]
    item_ids = []
    for attraction_id in attraction_ids:
        r = client.post(
            f"/api/itineraries/{trip_id}/items",
            json={"attraction_id": attraction_id, "day_number": day},
            headers=auth_headers,
        )
        item_ids.append(r.get_json()["item"]["id"])
    return trip_id, item_ids


# --- Success ------------------------------------------------------------------

def test_returns_totals_and_legs_for_a_day(client, auth_headers, monkeypatch):
    _stub_post(monkeypatch, _THREE_STOP_ROUTE)
    trip_id, item_ids = _make_trip(client, auth_headers)

    r = client.get(f"/api/itineraries/{trip_id}/days/1/route", headers=auth_headers)
    assert r.status_code == 200
    body = r.get_json()

    assert body["available"] is True
    assert body["day_number"] == 1
    assert body["route"]["total_distance_m"] == 154000
    assert body["route"]["total_duration_s"] == 12600
    assert [leg["duration_s"] for leg in body["route"]["legs"]] == [7200, 5400]
    assert [s["item_id"] for s in body["stops"]] == item_ids
    assert "suggested_item_order" not in body  # not an optimize request


def test_optimize_returns_suggested_item_order(client, auth_headers, monkeypatch, app):
    # A fourth located attraction so there are two intermediates to reorder.
    extra = Attraction(name="Ella Rock", category="Nature",
                       description="Hiking viewpoint.", latitude=6.86, longitude=81.05)
    db.session.add(extra)
    db.session.commit()

    calls = []
    _stub_post(monkeypatch, _OPTIMIZED_ROUTE, calls)
    trip_id, item_ids = _make_trip(client, auth_headers, attraction_ids=(1, 2, 3, extra.id))

    r = client.get(
        f"/api/itineraries/{trip_id}/days/1/route?optimize=true", headers=auth_headers
    )
    assert r.status_code == 200
    body = r.get_json()

    assert calls[0]["optimizeWaypointOrder"] is True
    # optimizedIntermediateWaypointIndex [1, 0] swaps the two middle stops.
    assert body["suggested_item_order"] == [
        item_ids[0], item_ids[2], item_ids[1], item_ids[3]
    ]
    assert body["route"]["total_duration_s"] == 10800


# --- Caching ------------------------------------------------------------------

def test_second_call_is_served_from_cache(client, auth_headers, monkeypatch):
    calls = []
    _stub_post(monkeypatch, _THREE_STOP_ROUTE, calls)
    trip_id, _ = _make_trip(client, auth_headers)

    first = client.get(f"/api/itineraries/{trip_id}/days/1/route", headers=auth_headers)
    assert first.get_json()["route"]["cached"] is False
    assert len(calls) == 1

    second = client.get(f"/api/itineraries/{trip_id}/days/1/route", headers=auth_headers)
    assert second.get_json()["route"]["cached"] is True
    assert len(calls) == 1  # same ordered stops — no refetch


# --- Failure handling ---------------------------------------------------------

def test_upstream_failure_returns_friendly_503(client, auth_headers, monkeypatch):
    def boom(body, headers):
        raise directions_service.DirectionsUnavailable(
            "Could not reach the routing service."
        )

    monkeypatch.setattr(directions_service, "_post_json", boom)
    trip_id, _ = _make_trip(client, auth_headers)

    r = client.get(f"/api/itineraries/{trip_id}/days/1/route", headers=auth_headers)
    assert r.status_code == 503
    body = r.get_json()
    assert body["available"] is False
    assert "error" in body


def test_missing_api_key_returns_503(client, auth_headers, monkeypatch, app):
    app.config["GOOGLE_MAPS_API_KEY"] = ""
    _stub_post(monkeypatch, _THREE_STOP_ROUTE)  # never reached — key check first
    trip_id, _ = _make_trip(client, auth_headers)

    r = client.get(f"/api/itineraries/{trip_id}/days/1/route", headers=auth_headers)
    assert r.status_code == 503
    assert r.get_json()["available"] is False


# --- Input validation / ownership ---------------------------------------------

def test_day_with_too_few_located_stops_returns_400(client, auth_headers, monkeypatch):
    _stub_post(monkeypatch, _THREE_STOP_ROUTE)
    trip_id, _ = _make_trip(client, auth_headers, attraction_ids=(1,))
    r = client.get(f"/api/itineraries/{trip_id}/days/1/route", headers=auth_headers)
    assert r.status_code == 400

    # A day with no items at all behaves the same.
    r = client.get(f"/api/itineraries/{trip_id}/days/2/route", headers=auth_headers)
    assert r.status_code == 400


def test_other_users_itinerary_is_a_404(client, auth_headers, monkeypatch):
    _stub_post(monkeypatch, _THREE_STOP_ROUTE)
    trip_id, _ = _make_trip(client, auth_headers)
    r = client.get(
        f"/api/itineraries/{trip_id}/days/1/route",
        headers={"Authorization": "Bearer valid-user2"},
    )
    assert r.status_code == 404
