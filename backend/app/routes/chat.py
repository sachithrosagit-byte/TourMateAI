"""Chat endpoints backing the Chat page.

Routes (registered under ``/api``):
  - ``GET    /api/chat/sessions``         auth: list user's chat sessions
  - ``POST   /api/chat/sessions``         auth: create a new empty chat session
  - ``GET    /api/chat/sessions/<id>/history`` auth: session's stored conversation
  - ``DELETE /api/chat/sessions/<id>``    auth: delete a specific session
  - ``PATCH  /api/chat/sessions/<id>``    auth: rename a specific session
  - ``POST   /api/chat``                  auth: one chatbot turn (persisted)
"""

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy.orm import joinedload

from ..extensions import db
from ..models import Attraction, ChatLog, ChatSession
from ..services.ai_service import chatbot_reply
from .attractions import _serialize_attraction
from .auth import require_auth
from .helpers import json_error

chat_bp = Blueprint("chat", __name__)

MAX_MESSAGE_LENGTH = 2000
MAX_HISTORY_TURNS = 20
HISTORY_DEFAULT_LIMIT = 50
HISTORY_MAX_LIMIT = 200
_HISTORY_ROLES = ("user", "assistant")


def _source():
    return "mock" if current_app.config.get("USE_MOCK_AI", True) else "ai"


def _clean_history(raw):
    turns = []
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = item.get("role")
        content = item.get("content")
        if role in _HISTORY_ROLES and isinstance(content, str) and content.strip():
            turns.append({"role": role, "content": content})
    return turns[-MAX_HISTORY_TURNS:]


def _attractions_by_ids(ids, lookup=None):
    if not ids:
        return []
    if lookup is None:
        rows = Attraction.query.filter(Attraction.id.in_(ids)).all()
        lookup = {a.id: _serialize_attraction(a) for a in rows}
    return [lookup[i] for i in ids if i in lookup]


def _serialize_chat_log(log, lookup=None):
    return {
        "id": log.id,
        "message": log.message,
        "response": log.response,
        "suggested_attractions": _attractions_by_ids(
            log.suggested_attractions or [], lookup
        ),
        "created_at": log.created_at.isoformat() if log.created_at else None,
    }


def _serialize_chat_session(session):
    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }


@chat_bp.get("/chat/sessions")
@require_auth
def get_sessions():
    """Get all chat sessions for the current user."""
    sessions = ChatSession.query.filter_by(user_id=g.current_user.id).order_by(ChatSession.created_at.desc()).all()
    return jsonify({"sessions": [_serialize_chat_session(s) for s in sessions]})


@chat_bp.post("/chat/sessions")
@require_auth
def create_session():
    """Create a new empty chat session."""
    body = request.get_json(silent=True) or {}
    title = body.get("title", "New Chat")
    session = ChatSession(user_id=g.current_user.id, title=title)
    db.session.add(session)
    db.session.commit()
    return jsonify(_serialize_chat_session(session)), 201


@chat_bp.delete("/chat/sessions/<int:session_id>")
@require_auth
def delete_session(session_id):
    """Delete a chat session."""
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
    if not session:
        return json_error("Session not found", 404)
    db.session.delete(session)
    db.session.commit()
    return jsonify({"deleted": True})


@chat_bp.patch("/chat/sessions/<int:session_id>")
@require_auth
def rename_session(session_id):
    """Rename a chat session."""
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
    if not session:
        return json_error("Session not found", 404)
    
    body = request.get_json(silent=True) or {}
    title = body.get("title")
    if not isinstance(title, str) or not title.strip():
        return json_error("title is required and must be a non-empty string.", 400)
    
    session.title = title[:255].strip()
    db.session.commit()
    return jsonify(_serialize_chat_session(session))


@chat_bp.get("/chat/sessions/<int:session_id>/history")
@require_auth
def get_session_history(session_id):
    """Get the conversation history for a session."""
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
    if not session:
        return json_error("Session not found", 404)

    raw_limit = request.args.get("limit", str(HISTORY_DEFAULT_LIMIT))
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return json_error("limit must be an integer.", 400)
    if limit < 1:
        return json_error("limit must be positive.", 400)
    limit = min(limit, HISTORY_MAX_LIMIT)

    rows = (
        ChatLog.query.filter_by(session_id=session_id)
        .order_by(ChatLog.id.desc())
        .limit(limit)
        .all()
    )
    rows.reverse()

    all_ids = {i for row in rows for i in (row.suggested_attractions or [])}
    lookup = {}
    if all_ids:
        attractions = Attraction.query.filter(Attraction.id.in_(all_ids)).all()
        lookup = {a.id: _serialize_attraction(a) for a in attractions}

    return jsonify(
        {"messages": [_serialize_chat_log(row, lookup) for row in rows]}
    )


@chat_bp.post("/chat")
@require_auth
def send_message():
    """One chatbot turn for the current user, saved to ChatLogs.

    Body:
      - ``message``               required non-empty string (<= 2000 chars)
      - ``session_id``            required integer (must own session)
      - ``conversation_history``  optional list of prior turns
    """
    body = request.get_json(silent=True) or {}

    message = body.get("message")
    if not isinstance(message, str) or not message.strip():
        return json_error("message is required and must be a non-empty string.", 400)
    message = message.strip()
    if len(message) > MAX_MESSAGE_LENGTH:
        return json_error(
            f"message must be at most {MAX_MESSAGE_LENGTH} characters.", 400
        )
        
    session_id = body.get("session_id")
    if not isinstance(session_id, int):
        return json_error("session_id is required and must be an integer.", 400)
        
    session = ChatSession.query.filter_by(id=session_id, user_id=g.current_user.id).first()
    if not session:
        return json_error("Session not found", 404)

    raw_history = body.get("conversation_history")
    if raw_history is not None and not isinstance(raw_history, list):
        return json_error("conversation_history must be a list.", 400)
    history = _clean_history(raw_history or [])

    result = chatbot_reply(g.current_user.id, message, history or None)
    
    # Auto-generate title if this is the first message in a default-titled session
    is_first_message = ChatLog.query.filter_by(session_id=session.id).count() == 0
    if is_first_message and session.title == "New Chat":
        # simple title generation: first 30 chars of the message
        new_title = message[:30]
        if len(message) > 30:
            new_title += "..."
        session.title = new_title

    log = ChatLog(
        user_id=g.current_user.id,
        session_id=session.id,
        message=message,
        response=result["reply"],
        suggested_attractions=result["suggested_attractions"],
    )
    db.session.add(log)
    db.session.commit()

    return (
        jsonify(
            {
                "reply": result["reply"],
                "suggested_attractions": _attractions_by_ids(
                    result["suggested_attractions"]
                ),
                "chat_log_id": log.id,
                "created_at": log.created_at.isoformat() if log.created_at else None,
                "source": _source(),
                "session_title": session.title, # Pass back so frontend can update title instantly
            }
        ),
        201,
    )
