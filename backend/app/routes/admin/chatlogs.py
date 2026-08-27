"""Admin chatbot accuracy monitoring.

A first-class view over the ChatLogs table so an admin can watch how the RAG
chatbot is doing and flag weak answers for the AI teammate to retrain on.

  - ``GET   /chat-logs``          paginated transcripts (filters: flag, user_id,
                                  search)
  - ``GET   /chat-logs/volume``   message volume (and flag counts) per day
  - ``PATCH /chat-logs/<id>``     mark a reply's quality
                                  (``{ quality_flag: "unhelpful"|"incorrect"|null }``)
"""

from flask import jsonify, request
from sqlalchemy import func

from ...extensions import db
from ...models import ChatLog, User
from ...models.chat_log import QUALITY_FLAGS
from ..auth import require_admin
from ..helpers import json_error
from . import admin_bp
from ._shared import iso, parse_pagination

# ``flag`` filter values: a specific flag, plus the two set/unset buckets.
FLAG_FILTERS = QUALITY_FLAGS + ("flagged", "unflagged", "all")

# How many days of volume history the chart returns by default.
DEFAULT_VOLUME_DAYS = 30
MAX_VOLUME_DAYS = 365


def _serialize(log, user_name):
    return {
        "id": log.id,
        "user_id": log.user_id,
        "user_name": user_name,
        "message": log.message,
        "response": log.response,
        "suggested_attractions": log.suggested_attractions,
        "quality_flag": log.quality_flag,
        "created_at": iso(log.created_at),
    }


@admin_bp.get("/chat-logs")
@require_admin
def list_chat_logs():
    """Chatbot transcripts, newest first, paginated.

    Query params (all optional):
      - ``flag``      ``unhelpful`` / ``incorrect`` (a specific flag),
                      ``flagged`` (any flag set), ``unflagged`` (none), or ``all``
      - ``user_id``   only this user's messages
      - ``search``    substring match on the message OR the bot response
      - ``page`` / ``per_page``   pagination (default 20, max 100)
    """
    flag = (request.args.get("flag") or "all").strip().lower()
    if flag not in FLAG_FILTERS:
        return json_error(f"flag must be one of: {', '.join(FLAG_FILTERS)}.", 400)

    page, per_page, page_error = parse_pagination()
    if page_error:
        return page_error

    query = db.select(ChatLog, User.name).join(
        User, User.id == ChatLog.user_id, isouter=True
    )

    if flag in QUALITY_FLAGS:
        query = query.where(ChatLog.quality_flag == flag)
    elif flag == "flagged":
        query = query.where(ChatLog.quality_flag.isnot(None))
    elif flag == "unflagged":
        query = query.where(ChatLog.quality_flag.is_(None))

    raw_user_id = request.args.get("user_id")
    if raw_user_id:
        try:
            query = query.where(ChatLog.user_id == int(raw_user_id))
        except ValueError:
            return json_error("user_id must be an integer.", 400)

    search = (request.args.get("search") or "").strip()
    if search:
        pattern = f"%{search}%"
        query = query.where(
            db.or_(ChatLog.message.ilike(pattern), ChatLog.response.ilike(pattern))
        )

    query = query.order_by(ChatLog.created_at.desc(), ChatLog.id.desc())

    total = db.session.scalar(db.select(func.count()).select_from(query.subquery()))
    rows = db.session.execute(
        query.limit(per_page).offset((page - 1) * per_page)
    ).all()

    total_pages = (total + per_page - 1) // per_page
    return jsonify(
        {
            "chat_logs": [_serialize(log, user_name) for log, user_name in rows],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }
    )


@admin_bp.get("/chat-logs/volume")
@require_admin
def chat_volume():
    """Message volume per day (plus how many were flagged), oldest→newest.

    Query param ``days`` (default 30, max 365) bounds the window. Returns
    ``{ volume: [{date, count, flagged}], total, flagged_total }``.
    """
    raw_days = request.args.get("days", str(DEFAULT_VOLUME_DAYS))
    try:
        days = int(raw_days)
    except (TypeError, ValueError):
        return json_error("days must be an integer.", 400)
    if days < 1:
        return json_error("days must be positive.", 400)
    days = min(days, MAX_VOLUME_DAYS)

    day = func.date(ChatLog.created_at).label("day")
    flagged = func.sum(
        db.case((ChatLog.quality_flag.isnot(None), 1), else_=0)
    ).label("flagged")

    rows = db.session.execute(
        db.select(day, func.count(ChatLog.id), flagged)
        .group_by(day)
        .order_by(day.desc())
        .limit(days)
    ).all()

    # Query is newest-first (so ``days`` keeps the most recent); present oldest→newest.
    volume = [
        {"date": iso(d), "count": count, "flagged": int(flag_count or 0)}
        for d, count, flag_count in reversed(rows)
    ]

    totals = db.session.execute(
        db.select(
            func.count(ChatLog.id),
            func.sum(db.case((ChatLog.quality_flag.isnot(None), 1), else_=0)),
        )
    ).one()
    return jsonify(
        {
            "volume": volume,
            "total": totals[0],
            "flagged_total": int(totals[1] or 0),
        }
    )


@admin_bp.patch("/chat-logs/<int:log_id>")
@require_admin
def flag_chat_log(log_id):
    """Set (or clear) a reply's quality flag.

    Body: ``{ quality_flag: "unhelpful" | "incorrect" | null }``. ``null`` clears
    a previous flag.
    """
    log = db.session.get(ChatLog, log_id)
    if log is None:
        return json_error("Chat log not found.", 404)

    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return json_error("Request body must be a JSON object.", 400)
    if "quality_flag" not in body:
        return json_error("quality_flag is required (use null to clear).", 400)

    flag = body.get("quality_flag")
    if flag is not None and flag not in QUALITY_FLAGS:
        allowed = ", ".join(QUALITY_FLAGS)
        return json_error(f"quality_flag must be null or one of: {allowed}.", 400)

    log.quality_flag = flag
    db.session.commit()

    user_name = db.session.scalar(
        db.select(User.name).where(User.id == log.user_id)
    )
    return jsonify({"chat_log": _serialize(log, user_name)})
