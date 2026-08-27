"""Admin system-analytics dashboard.

  - ``GET /analytics``              headline totals + most-viewed (unchanged shape,
                                    backs the existing Overview panel)
  - ``GET /analytics/attractions``  most / least engaged + a recommendation
                                    click-through *proxy* from interaction signals
  - ``GET /analytics/feedback``     rating distribution (1–5) + hidden count
  - ``GET /analytics/chat``         chatbot volume + flag rate over time
  - ``GET /analytics/images``       landmark-upload volume over time + avg
                                    recognition confidence
"""

from flask import jsonify, request
from sqlalchemy import func

from ...extensions import db
from ...models import Attraction, ChatLog, Feedback, Interaction, UploadedImage, User
from ...models.interaction import InteractionType
from ..auth import require_admin
from ..helpers import json_error
from . import admin_bp
from ._shared import iso

# How many attractions the "most viewed" / engagement lists return.
MOST_VIEWED_LIMIT = 8
ENGAGEMENT_LIMIT = 8

DEFAULT_TIMESERIES_DAYS = 30
MAX_TIMESERIES_DAYS = 365


def _timeseries_days():
    """Read + validate the ``days`` window arg. Returns ``(days, error)``."""
    raw = request.args.get("days", str(DEFAULT_TIMESERIES_DAYS))
    try:
        days = int(raw)
    except (TypeError, ValueError):
        return None, json_error("days must be an integer.", 400)
    if days < 1:
        return None, json_error("days must be positive.", 400)
    return min(days, MAX_TIMESERIES_DAYS), None


# ---------------------------------------------------------------------------
# Headline (backward-compatible with the original /analytics)
# ---------------------------------------------------------------------------

@admin_bp.get("/analytics")
@require_admin
def analytics():
    """Dashboard numbers: headline totals + the most-viewed attractions.

    ``most_viewed`` counts only ``view`` interactions (likes/visits are separate
    signals); ordered desc, top MOST_VIEWED_LIMIT, ties broken by name so the
    chart is stable across reloads.
    """
    totals = {
        "users": db.session.scalar(db.select(func.count(User.id))),
        "attractions": db.session.scalar(db.select(func.count(Attraction.id))),
        "interactions": db.session.scalar(db.select(func.count(Interaction.id))),
        "chat_messages": db.session.scalar(db.select(func.count(ChatLog.id))),
        "feedback_count": db.session.scalar(db.select(func.count(Feedback.id))),
    }
    avg_rating = db.session.scalar(db.select(func.avg(Feedback.rating)))
    totals["avg_feedback_rating"] = (
        round(float(avg_rating), 2) if avg_rating is not None else None
    )

    view_ct = func.count(Interaction.id).label("views")
    most_viewed_rows = db.session.execute(
        db.select(Attraction.id, Attraction.name, Attraction.category, view_ct)
        .join(Interaction, Interaction.attraction_id == Attraction.id)
        .where(Interaction.interaction_type == InteractionType.view)
        .group_by(Attraction.id, Attraction.name, Attraction.category)
        .order_by(view_ct.desc(), Attraction.name.asc())
        .limit(MOST_VIEWED_LIMIT)
    ).all()

    most_viewed = [
        {
            "attraction_id": attraction_id,
            "name": name,
            "category": category,
            "views": views,
        }
        for attraction_id, name, category, views in most_viewed_rows
    ]

    return jsonify({"totals": totals, "most_viewed": most_viewed})


# ---------------------------------------------------------------------------
# Attraction engagement + recommendation CTR proxy
# ---------------------------------------------------------------------------

@admin_bp.get("/analytics/attractions")
@require_admin
def attraction_engagement():
    """Most / least engaged attractions + a recommendation click-through proxy.

    "Engagement" = total interactions of any type. The least-engaged list uses a
    left join so attractions with zero interactions surface (exactly what an
    admin wants to prune or promote).

    ``ctr_proxy`` approximates recommendation follow-through from the interaction
    funnel: of attractions that were *viewed*, how many were then *liked* or
    *visited*. We don't log an explicit "recommended" event, so this is a proxy,
    not a true CTR — ``rate = (likes + visits) / views``.
    """
    engagement_ct = func.count(Interaction.id).label("engagement")
    base = (
        db.select(Attraction.id, Attraction.name, Attraction.category, engagement_ct)
        .join(Interaction, Interaction.attraction_id == Attraction.id, isouter=True)
        .group_by(Attraction.id, Attraction.name, Attraction.category)
    )

    most_rows = db.session.execute(
        base.order_by(engagement_ct.desc(), Attraction.name.asc()).limit(ENGAGEMENT_LIMIT)
    ).all()
    least_rows = db.session.execute(
        base.order_by(engagement_ct.asc(), Attraction.name.asc()).limit(ENGAGEMENT_LIMIT)
    ).all()

    def _shape(rows):
        return [
            {
                "attraction_id": aid,
                "name": name,
                "category": category,
                "interactions": engagement,
            }
            for aid, name, category, engagement in rows
        ]

    # Interaction-type totals for the CTR proxy.
    type_counts = dict(
        db.session.execute(
            db.select(Interaction.interaction_type, func.count(Interaction.id)).group_by(
                Interaction.interaction_type
            )
        ).all()
    )
    views = type_counts.get(InteractionType.view, 0)
    likes = type_counts.get(InteractionType.like, 0)
    visits = type_counts.get(InteractionType.visit, 0)
    conversions = likes + visits
    ctr_proxy = {
        "views": views,
        "likes": likes,
        "visits": visits,
        "conversions": conversions,
        "rate": round(conversions / views, 4) if views else None,
    }

    return jsonify(
        {
            "most_engaged": _shape(most_rows),
            "least_engaged": _shape(least_rows),
            "ctr_proxy": ctr_proxy,
        }
    )


# ---------------------------------------------------------------------------
# Feedback rating distribution
# ---------------------------------------------------------------------------

@admin_bp.get("/analytics/feedback")
@require_admin
def feedback_distribution():
    """Rating distribution (1–5), average, and how many reviews are hidden."""
    counts = dict(
        db.session.execute(
            db.select(Feedback.rating, func.count(Feedback.id)).group_by(Feedback.rating)
        ).all()
    )
    distribution = [{"rating": r, "count": counts.get(r, 0)} for r in range(1, 6)]

    total = db.session.scalar(db.select(func.count(Feedback.id)))
    hidden = db.session.scalar(
        db.select(func.count(Feedback.id)).where(Feedback.is_hidden.is_(True))
    )
    avg = db.session.scalar(db.select(func.avg(Feedback.rating)))

    return jsonify(
        {
            "distribution": distribution,
            "total": total,
            "hidden": hidden,
            "average": round(float(avg), 2) if avg is not None else None,
        }
    )


# ---------------------------------------------------------------------------
# Chatbot volume + flag rate over time
# ---------------------------------------------------------------------------

@admin_bp.get("/analytics/chat")
@require_admin
def chat_analytics():
    """Per-day chat volume with flag counts + rate; plus overall flag rate.

    ``days`` (default 30, max 365) bounds the window. ``flag_rate`` per day is
    ``flagged / count``.
    """
    days, error = _timeseries_days()
    if error:
        return error

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

    series = [
        {
            "date": iso(d),
            "count": count,
            "flagged": int(flag_count or 0),
            "flag_rate": round(int(flag_count or 0) / count, 4) if count else 0,
        }
        for d, count, flag_count in reversed(rows)
    ]

    total = db.session.scalar(db.select(func.count(ChatLog.id)))
    flagged_total = db.session.scalar(
        db.select(func.count(ChatLog.id)).where(ChatLog.quality_flag.isnot(None))
    )
    return jsonify(
        {
            "series": series,
            "total": total,
            "flagged_total": flagged_total,
            "flag_rate": round(flagged_total / total, 4) if total else None,
        }
    )


# ---------------------------------------------------------------------------
# Landmark-recognition upload volume + confidence
# ---------------------------------------------------------------------------

@admin_bp.get("/analytics/images")
@require_admin
def image_analytics():
    """Landmark-upload volume per day + average recognition confidence.

    Confidence lives in the ``recognition_result`` JSON (see the ``/identify``
    contract) which SQLite can't aggregate portably, so we pull the values and
    average in Python. ``days`` (default 30, max 365) bounds the volume series.
    """
    days, error = _timeseries_days()
    if error:
        return error

    day = func.date(UploadedImage.created_at).label("day")
    rows = db.session.execute(
        db.select(day, func.count(UploadedImage.id))
        .group_by(day)
        .order_by(day.desc())
        .limit(days)
    ).all()
    series = [{"date": iso(d), "count": count} for d, count in reversed(rows)]

    total = db.session.scalar(db.select(func.count(UploadedImage.id)))

    # Average confidence across results that carry a numeric ``confidence``.
    results = db.session.scalars(
        db.select(UploadedImage.recognition_result).where(
            UploadedImage.recognition_result.isnot(None)
        )
    ).all()
    confidences = []
    for result in results:
        if isinstance(result, dict):
            value = result.get("confidence")
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                confidences.append(float(value))
    avg_confidence = round(sum(confidences) / len(confidences), 4) if confidences else None

    return jsonify(
        {
            "series": series,
            "total": total,
            "recognized_count": len(confidences),
            "avg_confidence": avg_confidence,
        }
    )
