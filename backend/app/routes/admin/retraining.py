"""Admin "Retraining & Dataset" controls.

The AI models are the teammate's module, so this doesn't trigger a real training
run. Instead it surfaces the dataset's current state and records a
``retraining_request`` audit action the teammate can later hook up to their real
pipeline.

  - ``GET  /retraining/stats``     dataset snapshot + what's accumulated since the
                                   last retraining request
  - ``POST /retraining/request``   log a retraining-request AdminAction
  - ``GET  /retraining/history``   paginated audit trail of retraining requests
"""

from flask import g, jsonify, request
from sqlalchemy import func

from ...extensions import db
from ...models import AdminAction, Attraction, ChatLog, Feedback, Interaction, User
from ...models.admin_action import RETRAINING_REQUEST
from ..auth import require_admin
from ..helpers import json_error
from . import admin_bp
from ._shared import iso, parse_pagination

NOTES_MAX_LEN = 1000


def _serialize_action(action, admin_name=None, admin_email=None):
    return {
        "id": action.id,
        "admin_id": action.admin_id,
        "admin_name": admin_name,
        "admin_email": admin_email,
        "action_type": action.action_type,
        "notes": action.notes,
        "created_at": iso(action.created_at),
    }


def _last_retraining_request():
    """The most recent ``retraining_request`` AdminAction, or None."""
    return db.session.scalar(
        db.select(AdminAction)
        .where(AdminAction.action_type == RETRAINING_REQUEST)
        .order_by(AdminAction.created_at.desc(), AdminAction.id.desc())
        .limit(1)
    )


@admin_bp.get("/retraining/stats")
@require_admin
def retraining_stats():
    """Dataset snapshot for the retraining panel.

    Reports the full totals plus how much *new* signal has arrived since the last
    retraining request (so the admin can judge whether another run is worthwhile).
    """
    last = _last_retraining_request()
    since = last.created_at if last else None

    def _count(model, extra=None):
        query = db.select(func.count(model.id))
        if since is not None:
            query = query.where(model.created_at > since)
        if extra is not None:
            query = query.where(extra)
        return db.session.scalar(query)

    stats = {
        "total_attractions": db.session.scalar(db.select(func.count(Attraction.id))),
        "total_users": db.session.scalar(db.select(func.count(User.id))),
        "total_feedback": db.session.scalar(db.select(func.count(Feedback.id))),
        "total_interactions": db.session.scalar(db.select(func.count(Interaction.id))),
        "total_chat_messages": db.session.scalar(db.select(func.count(ChatLog.id))),
        "flagged_chat_responses": db.session.scalar(
            db.select(func.count(ChatLog.id)).where(ChatLog.quality_flag.isnot(None))
        ),
        # New signal accumulated since the last retraining request (all-time if
        # none has been made yet).
        "feedback_since_last_request": _count(Feedback),
        "interactions_since_last_request": _count(Interaction),
        "chat_messages_since_last_request": _count(ChatLog),
    }

    last_payload = None
    if last is not None:
        last_payload = _serialize_action(
            last,
            admin_name=last.admin.name if last.admin else None,
            admin_email=last.admin.email if last.admin else None,
        )

    return jsonify({"stats": stats, "last_retraining_request": last_payload})


@admin_bp.post("/retraining/request")
@require_admin
def request_retraining():
    """Log a retraining request (audit only — no real training runs yet).

    Body: ``{ notes?: str }`` — an optional reason. Returns the new AdminAction,
    201. The AI teammate watches these rows / ``GET /retraining/history`` to wire
    up the real pipeline later.
    """
    body = request.get_json(silent=True) or {}
    notes = body.get("notes")
    if notes is not None and not isinstance(notes, str):
        return json_error("notes must be a string.", 400)
    if isinstance(notes, str):
        notes = notes.strip() or None
        if notes and len(notes) > NOTES_MAX_LEN:
            return json_error(
                f"notes must be at most {NOTES_MAX_LEN} characters.", 400
            )

    action = AdminAction(
        admin_id=g.current_user.id,
        action_type=RETRAINING_REQUEST,
        notes=notes,
    )
    db.session.add(action)
    db.session.commit()

    return jsonify(
        {
            "action": _serialize_action(
                action,
                admin_name=g.current_user.name,
                admin_email=g.current_user.email,
            )
        }
    ), 201


@admin_bp.get("/retraining/history")
@require_admin
def retraining_history():
    """Paginated audit trail of retraining requests, newest first."""
    page, per_page, page_error = parse_pagination()
    if page_error:
        return page_error

    query = (
        db.select(AdminAction, User.name, User.email)
        .join(User, User.id == AdminAction.admin_id, isouter=True)
        .where(AdminAction.action_type == RETRAINING_REQUEST)
        .order_by(AdminAction.created_at.desc(), AdminAction.id.desc())
    )

    total = db.session.scalar(db.select(func.count()).select_from(query.subquery()))
    rows = db.session.execute(
        query.limit(per_page).offset((page - 1) * per_page)
    ).all()

    total_pages = (total + per_page - 1) // per_page
    return jsonify(
        {
            "actions": [
                _serialize_action(action, admin_name=name, admin_email=email)
                for action, name, email in rows
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }
    )


@admin_bp.post("/retraining/ingest_fares")
@require_admin
def ingest_fares_endpoint():
    """Trigger the manual ingestion of NTC bus fares."""
    try:
        import sys
        import os
        import subprocess
        
        script_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))), "scripts", "ingest_fares.py")
        
        result = subprocess.run([sys.executable, script_path], capture_output=True, text=True)
        
        if result.returncode == 0:
            return jsonify({"status": "success", "message": "Fares ingested successfully.", "log": result.stdout})
        else:
            return jsonify({"status": "error", "message": "Fares ingestion failed.", "log": result.stderr}), 500
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500
