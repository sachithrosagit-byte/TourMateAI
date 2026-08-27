"""Admin user & interaction management.

  - ``GET /users``        paginated user list with search + signup-date + activity
                          filters, each row carrying interaction/feedback counts
  - ``GET /users/<id>``   one user's profile plus their full interaction and
                          feedback history (for support / moderation context)
"""

from flask import jsonify, request
from sqlalchemy import func

from ...extensions import db
from ...models import Attraction, Feedback, Interaction, User
from ..auth import require_admin
from ..helpers import json_error
from . import admin_bp
from ._shared import iso, parse_date_arg, parse_pagination

# ``activity`` filter buckets, by total interactions logged.
ACTIVITY_LEVELS = ("active", "inactive")
ACTIVE_MIN_INTERACTIONS = 1

# Cap the per-user history lists so one heavy user can't return thousands of rows.
HISTORY_LIMIT = 100


def _activity_counts_subqueries():
    """Correlated scalar subqueries for a user's interaction + feedback counts."""
    interactions_ct = (
        db.select(func.count(Interaction.id))
        .where(Interaction.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    feedback_ct = (
        db.select(func.count(Feedback.id))
        .where(Feedback.user_id == User.id)
        .correlate(User)
        .scalar_subquery()
    )
    return interactions_ct, feedback_ct


@admin_bp.get("/users")
@require_admin
def list_users():
    """Users, newest first, paginated, with activity counts.

    Query params (all optional):
      - ``search``        substring match on name OR email (case-insensitive)
      - ``created_from`` / ``created_to``   signup-date range (YYYY-MM-DD; ``to``
                          is inclusive of the whole day)
      - ``activity``      ``active`` (≥1 interaction) or ``inactive`` (none)
      - ``page`` / ``per_page``   pagination (default 20, max 100)

    Counts come from correlated scalar subqueries (not joins) so one user with
    many interactions can't multiply their feedback rows into a wrong count.
    """
    interactions_ct, feedback_ct = _activity_counts_subqueries()

    search = (request.args.get("search") or "").strip()
    created_from, err = parse_date_arg("created_from")
    if err:
        return err
    created_to, err = parse_date_arg("created_to")
    if err:
        return err
    activity = (request.args.get("activity") or "").strip().lower()
    if activity and activity not in ACTIVITY_LEVELS:
        return json_error(
            f"activity must be one of: {', '.join(ACTIVITY_LEVELS)}.", 400
        )

    page, per_page, page_error = parse_pagination()
    if page_error:
        return page_error

    query = db.select(User, interactions_ct.label("ic"), feedback_ct.label("fc"))

    if search:
        pattern = f"%{search}%"
        query = query.where(
            db.or_(User.name.ilike(pattern), User.email.ilike(pattern))
        )
    if created_from:
        query = query.where(User.created_at >= created_from)
    if created_to:
        # Inclusive of the whole `created_to` day.
        query = query.where(func.date(User.created_at) <= created_to.date())
    if activity == "active":
        query = query.where(interactions_ct >= ACTIVE_MIN_INTERACTIONS)
    elif activity == "inactive":
        query = query.where(interactions_ct == 0)

    query = query.order_by(User.created_at.desc(), User.id.desc())

    # Count matching rows via a subquery so the WHERE/HAVING filters apply.
    total = db.session.scalar(
        db.select(func.count()).select_from(query.subquery())
    )
    rows = db.session.execute(
        query.limit(per_page).offset((page - 1) * per_page)
    ).all()

    users = [
        {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "is_admin": bool(user.is_admin),
            "role": "admin" if user.is_admin else "user",
            "preferences": user.preferences,
            "interactions_count": interactions,
            "feedback_count": feedback,
            "created_at": iso(user.created_at),
        }
        for user, interactions, feedback in rows
    ]
    total_pages = (total + per_page - 1) // per_page
    return jsonify(
        {
            "users": users,
            "pagination": {
                "page": page,
                "per_page": per_page,
                "total": total,
                "total_pages": total_pages,
            },
        }
    )


@admin_bp.get("/users/<int:user_id>")
@require_admin
def user_detail(user_id):
    """One user with their full interaction + feedback history.

    Lists are capped at ``HISTORY_LIMIT`` most-recent rows each and joined to
    attraction names so the admin can read them without extra lookups.
    """
    user = db.session.get(User, user_id)
    if user is None:
        return json_error("User not found.", 404)

    interaction_rows = db.session.execute(
        db.select(Interaction, Attraction.name)
        .join(Attraction, Attraction.id == Interaction.attraction_id, isouter=True)
        .where(Interaction.user_id == user_id)
        .order_by(Interaction.created_at.desc(), Interaction.id.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    interactions = [
        {
            "id": interaction.id,
            "attraction_id": interaction.attraction_id,
            "attraction_name": name,
            "interaction_type": (
                interaction.interaction_type.value
                if interaction.interaction_type
                else None
            ),
            "created_at": iso(interaction.created_at),
        }
        for interaction, name in interaction_rows
    ]

    feedback_rows = db.session.execute(
        db.select(Feedback, Attraction.name)
        .join(Attraction, Attraction.id == Feedback.attraction_id, isouter=True)
        .where(Feedback.user_id == user_id)
        .order_by(Feedback.created_at.desc(), Feedback.id.desc())
        .limit(HISTORY_LIMIT)
    ).all()
    feedback = [
        {
            "id": review.id,
            "attraction_id": review.attraction_id,
            "attraction_name": name,
            "rating": review.rating,
            "comment": review.comment,
            "is_hidden": bool(review.is_hidden),
            "created_at": iso(review.created_at),
        }
        for review, name in feedback_rows
    ]

    # True totals (the lists above are capped at HISTORY_LIMIT).
    interactions_total = db.session.scalar(
        db.select(func.count(Interaction.id)).where(Interaction.user_id == user_id)
    )
    feedback_total = db.session.scalar(
        db.select(func.count(Feedback.id)).where(Feedback.user_id == user_id)
    )

    return jsonify(
        {
            "user": {
                "id": user.id,
                "name": user.name,
                "email": user.email,
                "is_admin": bool(user.is_admin),
                "role": "admin" if user.is_admin else "user",
                "preferences": user.preferences,
                "created_at": iso(user.created_at),
                "interactions_count": interactions_total,
                "feedback_count": feedback_total,
            },
            "interactions": interactions,
            "feedback": feedback,
        }
    )
