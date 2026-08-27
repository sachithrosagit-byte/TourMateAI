"""Image upload + landmark recognition endpoints backing the Identify page.

Recognition itself is a thin HTTP wrapper: the vision logic — a random-pick
mock today, the real CNN classifier later — lives behind
``services.ai_service.recognize_image()``, so swapping the mock for the real
model is a config flip (``USE_MOCK_AI``), not a change here.

What this module adds on top of the service call:
  - **storage** — the uploaded file is saved under ``UPLOAD_FOLDER`` (local
    disk for the prototype; swap for cloud storage here without touching
    callers) with a random unguessable name,
  - **persistence** — every upload becomes an UploadedImages row holding the
    stored file's URL plus the full recognition result, which is what powers
    the "your previous identifications" history on the page.

The service returns ``matched_attraction_id`` as a bare id (its contract);
these routes expand it into a full serialized attraction so the frontend can
link straight to the detail page without a second round-trip.

Routes (registered under ``/api``):
  - ``POST /api/images/recognize``        auth: upload a photo, get it identified
  - ``GET  /api/images``                  auth: the user's past uploads + results
  - ``GET  /api/images/uploads/<name>``   public: serve a stored image file
"""

import os
import uuid

from flask import Blueprint, current_app, g, jsonify, request, send_from_directory

from ..extensions import db
from ..models import Attraction, UploadedImage
from ..services.ai_service import recognize_image
from .attractions import _serialize_attraction
from .auth import require_auth
from .helpers import json_error

images_bp = Blueprint("images", __name__)

# Formats the (future) vision model can decode; keep client-side `accept` in sync.
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}

HISTORY_DEFAULT_LIMIT = 20
HISTORY_MAX_LIMIT = 100


def _source():
    """Which implementation answered — mirrors routes/chat.py."""
    return "mock" if current_app.config.get("USE_MOCK_AI", True) else "ai"


def _extension(filename):
    """Lower-cased extension without the dot, or '' when there isn't one."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _attraction_lookup(ids):
    """id -> serialized attraction for every resolvable id in ``ids``."""
    ids = [i for i in ids if i is not None]
    if not ids:
        return {}
    rows = Attraction.query.filter(Attraction.id.in_(ids)).all()
    return {a.id: _serialize_attraction(a) for a in rows}


def _serialize_upload(row, lookup):
    """Shape an UploadedImage row for JSON (upload response + history items).

    The recognition fields are flattened out of the stored JSON so the frontend
    reads one level deep; ``matched_attraction`` is the expanded attraction (or
    None when unmatched / since deleted).
    """
    result = row.recognition_result or {}
    return {
        "id": row.id,
        "image_url": row.image_url,
        "identified_name": result.get("identified_name"),
        "confidence": result.get("confidence"),
        "description": result.get("description"),
        "matched_attraction": lookup.get(result.get("matched_attraction_id")),
        "created_at": row.created_at.isoformat() if row.created_at else None,
    }


@images_bp.post("/images/recognize")
@require_auth
def recognize():
    """Identify a landmark from an uploaded photo, saving upload + result.

    multipart/form-data with the file under field name ``image`` (jpg / jpeg /
    png / webp; bodies over ``MAX_CONTENT_LENGTH`` are rejected with 413).

    Returns the stored upload with its recognition result — the same shape
    history items use — plus ``source`` (mock vs real model).
    """
    file = request.files.get("image")
    if file is None or not file.filename:
        return json_error(
            'An image file is required (multipart field name "image").', 400
        )

    ext = _extension(file.filename)
    if ext not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_EXTENSIONS))
        return json_error(f"Unsupported image type; use one of: {allowed}.", 400)

    result = recognize_image(file)

    # The recognizer may have consumed the stream — rewind before persisting.
    file.stream.seek(0)
    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = current_app.config["UPLOAD_FOLDER"]
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    upload = UploadedImage(
        user_id=g.current_user.id,
        image_url=f"/api/images/uploads/{filename}",
        recognition_result=result,
    )
    db.session.add(upload)
    db.session.commit()

    lookup = _attraction_lookup([result.get("matched_attraction_id")])
    payload = _serialize_upload(upload, lookup)
    payload["source"] = _source()
    return jsonify(payload), 201


@images_bp.get("/images")
@require_auth
def list_uploads():
    """The current user's uploads with their recognition results, newest first.

    Query params:
      - ``limit``  max uploads to return (default 20, capped at 100).
    """
    raw_limit = request.args.get("limit", str(HISTORY_DEFAULT_LIMIT))
    try:
        limit = int(raw_limit)
    except (TypeError, ValueError):
        return json_error("limit must be an integer.", 400)
    if limit < 1:
        return json_error("limit must be positive.", 400)
    limit = min(limit, HISTORY_MAX_LIMIT)

    rows = (
        UploadedImage.query.filter_by(user_id=g.current_user.id)
        .order_by(UploadedImage.id.desc())
        .limit(limit)
        .all()
    )

    # One attraction query for the whole page of history, shared by every row.
    lookup = _attraction_lookup(
        (row.recognition_result or {}).get("matched_attraction_id") for row in rows
    )

    return jsonify({"images": [_serialize_upload(row, lookup) for row in rows]})


@images_bp.get("/images/uploads/<path:filename>")
def serve_upload(filename):
    """Serve a stored upload so ``<img src>`` can render it.

    Deliberately unauthenticated: browsers can't attach the Firebase bearer
    token to image requests. Filenames are random 128-bit hex (unguessable),
    which is adequate privacy for this prototype; a production build would
    serve signed URLs from cloud storage instead.
    """
    # send_from_directory guards against path traversal in ``filename``.
    return send_from_directory(current_app.config["UPLOAD_FOLDER"], filename)
