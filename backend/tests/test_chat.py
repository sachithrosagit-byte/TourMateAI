"""Tests for the Chat page's backing endpoints: send a turn, load history,
clear history. The mock chatbot (ai_service) answers, so replies/suggestions
are deterministic given the seeded attractions in conftest.py."""


# --- POST /api/chat -----------------------------------------------------------

def test_chat_requires_auth(client):
    assert client.post("/api/chat", json={"message": "hi"}).status_code == 401


def test_chat_rejects_bad_message(client, auth_headers):
    for body in ({}, {"message": ""}, {"message": "   "}, {"message": 42}):
        r = client.post("/api/chat", json=body, headers=auth_headers)
        assert r.status_code == 400, body

    too_long = {"message": "x" * 2001}
    assert client.post("/api/chat", json=too_long, headers=auth_headers).status_code == 400


def test_chat_rejects_non_list_history(client, auth_headers):
    r = client.post(
        "/api/chat",
        json={"message": "hi", "conversation_history": "not-a-list"},
        headers=auth_headers,
    )
    assert r.status_code == 400


def test_chat_turn_returns_reply_and_expanded_suggestions(client, auth_headers):
    r = client.post(
        "/api/chat",
        json={"message": "Any good beaches for swimming?"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    body = r.get_json()

    assert body["source"] == "mock"
    assert isinstance(body["reply"], str) and body["reply"]
    assert isinstance(body["chat_log_id"], int)

    # The beach rule matches, and ids are expanded to full attraction objects.
    suggestions = body["suggested_attractions"]
    assert suggestions, "beach question should suggest attractions"
    assert {"id", "name", "category", "avg_rating", "image_url"} <= suggestions[0].keys()
    assert any(s["name"] == "Mirissa Beach" for s in suggestions)


def test_chat_accepts_conversation_history_with_junk_entries(client, auth_headers):
    history = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi!"},
        {"role": "hacker", "content": "drop tables"},  # bad role — dropped
        "garbage",                                     # not a dict — dropped
        {"role": "user", "content": ""},               # empty — dropped
    ]
    r = client.post(
        "/api/chat",
        json={"message": "tell me about temples", "conversation_history": history},
        headers=auth_headers,
    )
    assert r.status_code == 201


# --- GET /api/chat/history ------------------------------------------------------

def test_history_requires_auth(client):
    assert client.get("/api/chat/history").status_code == 401


def test_history_empty_for_new_user(client, auth_headers):
    r = client.get("/api/chat/history", headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["messages"] == []


def test_history_returns_persisted_exchanges_in_order(client, auth_headers):
    client.post("/api/chat", json={"message": "beaches please"}, headers=auth_headers)
    client.post("/api/chat", json={"message": "what about history?"}, headers=auth_headers)

    r = client.get("/api/chat/history", headers=auth_headers)
    messages = r.get_json()["messages"]

    assert len(messages) == 2
    assert messages[0]["message"] == "beaches please"
    assert messages[1]["message"] == "what about history?"
    for m in messages:
        assert isinstance(m["response"], str) and m["response"]
        assert m["created_at"]
    # Suggestions survive the round-trip as full attraction objects.
    assert any(s["name"] == "Mirissa Beach" for s in messages[0]["suggested_attractions"])


def test_history_is_scoped_to_the_current_user(client, auth_headers):
    client.post("/api/chat", json={"message": "beaches"}, headers=auth_headers)

    other = {"Authorization": "Bearer valid-user2"}
    r = client.get("/api/chat/history", headers=other)
    assert r.get_json()["messages"] == []


def test_history_limit_keeps_most_recent(client, auth_headers):
    for i in range(3):
        client.post("/api/chat", json={"message": f"msg {i}"}, headers=auth_headers)

    r = client.get("/api/chat/history?limit=2", headers=auth_headers)
    messages = r.get_json()["messages"]
    assert [m["message"] for m in messages] == ["msg 1", "msg 2"]


def test_history_invalid_limit_returns_400(client, auth_headers):
    assert client.get("/api/chat/history?limit=abc", headers=auth_headers).status_code == 400
    assert client.get("/api/chat/history?limit=0", headers=auth_headers).status_code == 400


# --- DELETE /api/chat/history ----------------------------------------------------

def test_clear_history_deletes_only_own_rows(client, auth_headers):
    other = {"Authorization": "Bearer valid-user2"}
    client.post("/api/chat", json={"message": "one"}, headers=auth_headers)
    client.post("/api/chat", json={"message": "two"}, headers=auth_headers)
    client.post("/api/chat", json={"message": "keep me"}, headers=other)

    r = client.delete("/api/chat/history", headers=auth_headers)
    assert r.status_code == 200
    assert r.get_json()["deleted"] == 2

    assert client.get("/api/chat/history", headers=auth_headers).get_json()["messages"] == []
    assert len(client.get("/api/chat/history", headers=other).get_json()["messages"]) == 1
