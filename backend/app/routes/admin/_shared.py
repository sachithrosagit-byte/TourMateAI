"""Helpers shared across the admin route modules.

Kept dependency-free of ``admin_bp`` (defined in ``__init__``) so importing this
from a route module never creates an import cycle.
"""

from datetime import datetime

from flask import request

from ...models import Attraction
from ..helpers import json_error

# Pagination guard-rails for the admin tables (users, feedback, chat logs,
# audit history). Mirrors routes/attractions.py so the whole API paginates
# consistently.
DEFAULT_PER_PAGE = 20
MAX_PER_PAGE = 100

# Field-length limits for attraction writes (create / update / CSV import).
NAME_MAX_LEN = 200
CATEGORY_MAX_LEN = 80
IMAGE_URL_MAX_LEN = 500


def parse_pagination():
    """Read + validate ``page``/``per_page`` query args.

    Returns ``(page, per_page, error)``; ``error`` is a Flask response tuple that
    is only truthy on invalid input, in which case the caller returns it as-is.
    """
    raw_page = request.args.get("page", "1")
    raw_per_page = request.args.get("per_page", str(DEFAULT_PER_PAGE))
    try:
        page = int(raw_page)
        per_page = int(raw_per_page)
    except (TypeError, ValueError):
        return None, None, json_error("page and per_page must be integers.", 400)
    if page < 1 or per_page < 1:
        return None, None, json_error("page and per_page must be positive.", 400)
    return page, min(per_page, MAX_PER_PAGE), None


def pagination_meta(pagination):
    """Standard pagination block for a Flask-SQLAlchemy ``Pagination`` object."""
    return {
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "total_pages": pagination.pages,
    }


def parse_date_arg(name):
    """Parse a ``YYYY-MM-DD`` query arg into a ``datetime`` (start of that day).

    Returns ``(datetime_or_None, error)``. Missing arg → ``(None, None)``.
    """
    raw = (request.args.get(name) or "").strip()
    if not raw:
        return None, None
    try:
        return datetime.strptime(raw, "%Y-%m-%d"), None
    except ValueError:
        return None, json_error(f"{name} must be a date in YYYY-MM-DD format.", 400)


def iso(value):
    """``datetime`` → ISO string, or ``None``. Also stringifies SQL ``date()`` output.

    ``func.date(...)`` returns a ``str`` on SQLite and a ``date`` on MySQL — both
    serialize cleanly by falling through to ``str()``.
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def serialize_attraction(attraction, review_count=None):
    """Full attraction row for the management table + edit form."""
    data = {
        "id": attraction.id,
        "name": attraction.name,
        "description": attraction.description,
        "category": attraction.category,
        "latitude": attraction.latitude,
        "longitude": attraction.longitude,
        "image_url": attraction.image_url,
        "avg_rating": round(attraction.avg_rating, 2) if attraction.avg_rating else 0,
        "created_at": iso(attraction.created_at),
    }
    if review_count is not None:
        data["review_count"] = review_count
    return data


def coerce_coord(value, field, low, high):
    """Validate an optional latitude/longitude. Returns ``(float_or_None, error)``."""
    if value is None or value == "":
        return None, None
    # bool is an int subclass — reject it before the float() cast masks it.
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None, json_error(f"{field} must be a number.", 400)
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None, json_error(f"{field} must be a number.", 400)
    if number < low or number > high:
        return None, json_error(f"{field} must be between {low} and {high}.", 400)
    return number, None


def validate_attraction_payload(body):
    """Validate a create/update body. Returns ``(clean_fields, error)``.

    Full-object semantics: the form always submits the complete attraction, so
    every field is validated together (no partial-update path).
    """
    if not isinstance(body, dict):
        return None, json_error("Request body must be a JSON object.", 400)

    name = body.get("name")
    if not isinstance(name, str) or not name.strip():
        return None, json_error("name is required.", 400)
    name = name.strip()
    if len(name) > NAME_MAX_LEN:
        return None, json_error(f"name must be at most {NAME_MAX_LEN} characters.", 400)

    def optional_str(field, max_len):
        value = body.get(field)
        if value is None:
            return None, None
        if not isinstance(value, str):
            return None, json_error(f"{field} must be a string.", 400)
        value = value.strip()
        if not value:
            return None, None
        if max_len and len(value) > max_len:
            return None, json_error(
                f"{field} must be at most {max_len} characters.", 400
            )
        return value, None

    category, err = optional_str("category", CATEGORY_MAX_LEN)
    if err:
        return None, err
    description, err = optional_str("description", None)
    if err:
        return None, err
    image_url, err = optional_str("image_url", IMAGE_URL_MAX_LEN)
    if err:
        return None, err

    latitude, err = coerce_coord(body.get("latitude"), "latitude", -90, 90)
    if err:
        return None, err
    longitude, err = coerce_coord(body.get("longitude"), "longitude", -180, 180)
    if err:
        return None, err

    return {
        "name": name,
        "category": category,
        "description": description,
        "image_url": image_url,
        "latitude": latitude,
        "longitude": longitude,
    }, None


def parse_id_list(value):
    """Validate an ``ids`` array from a JSON body. Returns ``(list[int], error)``.

    Accepts a non-empty list of positive ints (rejecting bools and duplicates
    collapse harmlessly). Used by the attraction bulk actions.
    """
    if not isinstance(value, list) or not value:
        return None, json_error("ids must be a non-empty array.", 400)
    ids = []
    for item in value:
        if isinstance(item, bool) or not isinstance(item, int) or item < 1:
            return None, json_error("ids must be an array of positive integers.", 400)
        ids.append(item)
    return ids, None
