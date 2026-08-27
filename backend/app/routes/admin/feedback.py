"""Admin feedback moderation.

Public attraction ratings/comments need a moderation path. This view lists every
review, lets an admin hide (soft) or delete (hard) inappropriate ones, and can
filter to just the hidden/visible set.

  - ``GET    /feedback``        paginated reviews (filters: hidden, attraction_id,
                                search, min/max rating)
  - ``PATCH  /feedback/<id>``   hide / unhide a review (``{ is_hidden: bool }``)
  - ``DELETE /feedback/<id>``   remove a review outright (recomputes the
                                attraction's stored avg_rating)

Note: ``is_hidden`` is stored but not yet subtracted from the public reviews /
avg_rating — that traveler-facing change is a deliberate follow-up so this pass
stays admin-only.
"""

from flask import jsonify, request
from sqlalchemy import func

from ...extensions import db
from ...models import Attraction, Feedback, User
from ..auth import require_admin
from ..helpers import json_error
from . import admin_bp
from ._shared import iso, parse_pagination

# ``hidden`` filter values.
HIDDEN_FILTERS = ("true", "false", "all")


def _serialize(review, user_name, attraction_name):
    return {
        "id": review.id,
        "user_id": review.user_id,
        "user_name": user_name,
        "attraction_id": review.attraction_id,
        "attraction_name": attraction_name,
        "rating": review.rating,
        "comment": review.comment,
        "is_hidden": bool(review.is_hidden),
        "created_at": iso(review.created_at),
    }


def _recompute_avg_rating(attraction_id):
    """Refresh ``Attraction.avg_rating`` after a review is deleted.

    Mirrors routes/attractions.py so the denormalised column the public list
    sorts on stays truthful. (Counts every remaining review — hidden ones still
    count publicly until the follow-up wires ``is_hidden`` into reads.)
    """
    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None:
        return
    avg = db.session.scalar(
        db.select(func.avg(Feedback.rating)).where(
            Feedback.attraction_id == attraction_id
        )
    )
    attraction.avg_rating = round(float(avg), 2) if avg is not None else 0


@admin_bp.get("/feedback")
@require_admin
def list_feedback():
    """All reviews, newest first, paginated.

    Query params (all optional):
      - ``hidden``          ``true`` / ``false`` / ``all`` (default ``all``)
      - ``attraction_id``   only reviews for this attraction
      - ``search``          substring match on the comment text
      - ``page`` / ``per_page``   pagination (default 20, max 100)
    """
    hidden = (request.args.get("hidden") or "all").strip().lower()
    if hidden not in HIDDEN_FILTERS:
        return json_error(f"hidden must be one of: {', '.join(HIDDEN_FILTERS)}.", 400)

    page, per_page, page_error = parse_pagination()
    if page_error:
        return page_error

    query = (
        db.select(Feedback, User.name, Attraction.name)
        .join(User, User.id == Feedback.user_id, isouter=True)
        .join(Attraction, Attraction.id == Feedback.attraction_id, isouter=True)
    )

    if hidden == "true":
        query = query.where(Feedback.is_hidden.is_(True))
    elif hidden == "false":
        query = query.where(Feedback.is_hidden.is_(False))

    raw_attraction_id = request.args.get("attraction_id")
    if raw_attraction_id:
        try:
            query = query.where(Feedback.attraction_id == int(raw_attraction_id))
        except ValueError:
            return json_error("attraction_id must be an integer.", 400)

    search = (request.args.get("search") or "").strip()
    if search:
        query = query.where(Feedback.comment.ilike(f"%{search}%"))

    query = query.order_by(Feedback.created_at.desc(), Feedback.id.desc())

    total = db.session.scalar(db.select(func.count()).select_from(query.subquery()))
    rows = db.session.execute(
        query.limit(per_page).offset((page - 1) * per_page)
    ).all()

    total_pages = (total + per_page - 1) // per_page
    return jsonify(
        {
            "feedback": [
                _serialize(review, user_name, attraction_name)
                for review, user_name, attraction_name in rows
            ],
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }
    )


@admin_bp.patch("/feedback/<int:feedback_id>")
@require_admin
def moderate_feedback(feedback_id):
    """Hide or unhide a review. Body: ``{ is_hidden: bool }``."""
    review = db.session.get(Feedback, feedback_id)
    if review is None:
        return json_error("Feedback not found.", 404)

    body = request.get_json(silent=True) or {}
    is_hidden = body.get("is_hidden")
    if not isinstance(is_hidden, bool):
        return json_error("is_hidden is required and must be a boolean.", 400)

    review.is_hidden = is_hidden
    db.session.commit()

    name_rows = db.session.execute(
        db.select(User.name, Attraction.name)
        .select_from(Feedback)
        .join(User, User.id == Feedback.user_id, isouter=True)
        .join(Attraction, Attraction.id == Feedback.attraction_id, isouter=True)
        .where(Feedback.id == feedback_id)
    ).first()
    user_name, attraction_name = name_rows if name_rows else (None, None)
    return jsonify({"feedback": _serialize(review, user_name, attraction_name)})


@admin_bp.delete("/feedback/<int:feedback_id>")
@require_admin
def delete_feedback(feedback_id):
    """Delete a review and refresh the attraction's stored average rating."""
    review = db.session.get(Feedback, feedback_id)
    if review is None:
        return json_error("Feedback not found.", 404)

    attraction_id = review.attraction_id
    db.session.delete(review)
    db.session.flush()  # make the row's absence visible to the aggregate
    _recompute_avg_rating(attraction_id)
    db.session.commit()
    return jsonify({"deleted": feedback_id})
