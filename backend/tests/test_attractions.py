"""Tests for the Attractions catalogue + interaction-logging API."""


# --- GET /api/attractions -------------------------------------------------

def test_list_returns_all(client):
    r = client.get("/api/attractions")
    assert r.status_code == 200
    body = r.get_json()
    assert body["pagination"]["total"] == 3
    assert len(body["attractions"]) == 3
    # serialized shape
    first = body["attractions"][0]
    assert {"id", "name", "category", "avg_rating"} <= first.keys()


def test_list_filter_by_category_is_case_insensitive(client):
    r = client.get("/api/attractions?category=beach")
    body = r.get_json()
    assert body["pagination"]["total"] == 1
    assert body["attractions"][0]["name"] == "Mirissa Beach"


def test_list_search_matches_name_or_description(client):
    # "fort" matches Galle Fort (name) and Sigiriya's "rock fortress" (description)
    r = client.get("/api/attractions?search=fort")
    assert r.get_json()["pagination"]["total"] == 2


def test_list_sort_by_name(client):
    r = client.get("/api/attractions?sort=name")
    names = [a["name"] for a in r.get_json()["attractions"]]
    assert names == sorted(names)


def test_list_invalid_sort_returns_400(client):
    r = client.get("/api/attractions?sort=bogus")
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_list_pagination(client):
    r = client.get("/api/attractions?per_page=2&page=1")
    body = r.get_json()
    assert len(body["attractions"]) == 2
    assert body["pagination"]["total_pages"] == 2

    r2 = client.get("/api/attractions?per_page=2&page=2")
    assert len(r2.get_json()["attractions"]) == 1


def test_list_invalid_pagination_returns_400(client):
    assert client.get("/api/attractions?page=abc").status_code == 400
    assert client.get("/api/attractions?page=0").status_code == 400
    assert client.get("/api/attractions?per_page=-5").status_code == 400


# --- GET /api/attractions/<id> --------------------------------------------

def test_detail_returns_attraction_with_rating_fields(client):
    r = client.get("/api/attractions/1")
    assert r.status_code == 200
    attraction = r.get_json()["attraction"]
    assert attraction["id"] == 1
    assert attraction["avg_rating"] == 0
    assert attraction["rating_count"] == 0
    assert attraction["reviews"] == []


def test_detail_missing_returns_404(client):
    r = client.get("/api/attractions/999")
    assert r.status_code == 404
    assert "error" in r.get_json()


# --- POST /api/attractions/<id>/feedback ----------------------------------

def test_feedback_requires_auth(client):
    r = client.post("/api/attractions/1/feedback", json={"rating": 5})
    assert r.status_code == 401
    # Auth failures use the same single-field error shape as every other endpoint.
    assert list(r.get_json().keys()) == ["error"]


def test_feedback_create_updates_average(client, auth_headers):
    r = client.post(
        "/api/attractions/1/feedback",
        headers=auth_headers,
        json={"rating": 5, "comment": "Amazing!"},
    )
    assert r.status_code == 201
    body = r.get_json()
    assert body["attraction_avg_rating"] == 5
    assert body["feedback"]["rating"] == 5
    assert body["feedback"]["comment"] == "Amazing!"

    # reflected in the detail endpoint
    detail = client.get("/api/attractions/1").get_json()["attraction"]
    assert detail["rating_count"] == 1
    assert len(detail["reviews"]) == 1


def test_feedback_from_two_users_averages(client, auth_headers):
    client.post("/api/attractions/1/feedback", headers=auth_headers, json={"rating": 5})
    r = client.post(
        "/api/attractions/1/feedback",
        headers={"Authorization": "Bearer valid-user2"},
        json={"rating": 3},
    )
    assert r.get_json()["attraction_avg_rating"] == 4  # (5 + 3) / 2


def test_feedback_same_user_updates_not_duplicates(client, auth_headers):
    client.post("/api/attractions/1/feedback", headers=auth_headers, json={"rating": 5})
    r = client.post("/api/attractions/1/feedback", headers=auth_headers, json={"rating": 1})
    assert r.status_code == 200  # update, not create
    assert r.get_json()["attraction_avg_rating"] == 1
    assert client.get("/api/attractions/1").get_json()["attraction"]["rating_count"] == 1


def test_feedback_invalid_rating_returns_400(client, auth_headers):
    for bad in ({"rating": 0}, {"rating": 6}, {"rating": "x"}, {"rating": True}, {}):
        r = client.post("/api/attractions/1/feedback", headers=auth_headers, json=bad)
        assert r.status_code == 400, bad
        assert "error" in r.get_json()


def test_feedback_missing_attraction_returns_404(client, auth_headers):
    r = client.post("/api/attractions/999/feedback", headers=auth_headers, json={"rating": 5})
    assert r.status_code == 404


# --- POST /api/interactions -----------------------------------------------

def test_interaction_create(client, auth_headers):
    r = client.post(
        "/api/interactions",
        headers=auth_headers,
        json={"attraction_id": 2, "interaction_type": "view"},
    )
    assert r.status_code == 201
    interaction = r.get_json()["interaction"]
    assert interaction["attraction_id"] == 2
    assert interaction["interaction_type"] == "view"
    # user comes from the token, never the body
    assert interaction["user_id"] is not None


def test_interaction_requires_auth(client):
    r = client.post(
        "/api/interactions", json={"attraction_id": 2, "interaction_type": "view"}
    )
    assert r.status_code == 401


def test_interaction_ignores_client_supplied_user_id(client, auth_headers):
    # A malicious body user_id must not override the authenticated user.
    r = client.post(
        "/api/interactions",
        headers=auth_headers,
        json={"attraction_id": 2, "interaction_type": "like", "user_id": 9999},
    )
    assert r.status_code == 201
    assert r.get_json()["interaction"]["user_id"] != 9999


def test_interaction_invalid_type_returns_400(client, auth_headers):
    r = client.post(
        "/api/interactions",
        headers=auth_headers,
        json={"attraction_id": 2, "interaction_type": "bookmark"},
    )
    assert r.status_code == 400
    assert "error" in r.get_json()


def test_interaction_missing_fields_returns_400(client, auth_headers):
    assert client.post(
        "/api/interactions", headers=auth_headers, json={"interaction_type": "like"}
    ).status_code == 400
    assert client.post(
        "/api/interactions", headers=auth_headers, json={"attraction_id": 2}
    ).status_code == 400


def test_interaction_missing_attraction_returns_404(client, auth_headers):
    r = client.post(
        "/api/interactions",
        headers=auth_headers,
        json={"attraction_id": 999, "interaction_type": "like"},
    )
    assert r.status_code == 404
