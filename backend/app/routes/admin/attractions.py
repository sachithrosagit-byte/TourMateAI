"""Admin attraction-catalogue management.

  - ``GET    /attractions``                whole catalogue for the table
  - ``POST   /attractions``                create one
  - ``PUT    /attractions/<id>``           update one
  - ``DELETE /attractions/<id>``           delete one (cascades interactions,
                                           feedback, itinerary items)
  - ``POST   /attractions/bulk-category``  reassign category for many
  - ``POST   /attractions/bulk-delete``    delete many
  - ``GET    /attractions/export.csv``     download the catalogue as CSV
  - ``POST   /attractions/import``         upload a CSV to create/update in bulk
  - ``POST   /attractions/upload-image``   upload a photo from disk
  - ``GET    /attractions/uploads/<name>`` serve a stored photo
"""

import csv
import io
import os
import uuid

from flask import Response, current_app, jsonify, request, send_from_directory
from sqlalchemy import func

from ...extensions import db
from ...models import Attraction, Feedback
from ..auth import require_admin
from ..helpers import json_error
from . import admin_bp
from ._shared import (
    CATEGORY_MAX_LEN,
    parse_id_list,
    serialize_attraction,
    validate_attraction_payload,
)

# Formats accepted for attraction photo uploads (mirrors routes/images.py).
ALLOWED_IMAGE_EXTENSIONS = {"jpg", "jpeg", "png", "webp"}
# Attraction photos live in their own subfolder of UPLOAD_FOLDER, separate from
# the landmark-recognition uploads in routes/images.py.
ATTRACTION_UPLOAD_SUBDIR = "attractions"

# Columns emitted by the CSV export and understood by the import (in this order).
CSV_COLUMNS = ["id", "name", "category", "description", "latitude", "longitude", "image_url"]

# Cap CSV import rows so a giant upload can't stall a request (prototype scope).
MAX_IMPORT_ROWS = 1000


def _image_extension(filename):
    """Lower-cased extension without the dot, or '' when there isn't one."""
    return filename.rsplit(".", 1)[-1].lower() if "." in filename else ""


def _review_count_subquery():
    """Correlated scalar subquery counting an attraction's reviews."""
    return (
        db.select(func.count(Feedback.id))
        .where(Feedback.attraction_id == Attraction.id)
        .correlate(Attraction)
        .scalar_subquery()
    )


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@admin_bp.get("/attractions")
@require_admin
def list_attractions():
    """Whole catalogue (no pagination — admin table wants everything), A→Z.

    Each row carries its review count so the table can show engagement without a
    per-row round-trip.
    """
    rows = db.session.execute(
        db.select(Attraction, _review_count_subquery()).order_by(Attraction.name.asc())
    ).all()
    return jsonify(
        {
            "attractions": [
                serialize_attraction(a, review_count=count) for a, count in rows
            ]
        }
    )


@admin_bp.post("/attractions")
@require_admin
def create_attraction():
    """Create an attraction. Body: ``{name, category?, description?, latitude?,
    longitude?, image_url?}``. Returns the new row, 201."""
    fields, error = validate_attraction_payload(request.get_json(silent=True))
    if error:
        return error

    attraction = Attraction(**fields)
    db.session.add(attraction)
    db.session.commit()
    return jsonify({"attraction": serialize_attraction(attraction, review_count=0)}), 201


@admin_bp.put("/attractions/<int:attraction_id>")
@require_admin
def update_attraction(attraction_id):
    """Replace an attraction's editable fields (same body as create)."""
    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None:
        return json_error("Attraction not found.", 404)

    fields, error = validate_attraction_payload(request.get_json(silent=True))
    if error:
        return error

    for key, value in fields.items():
        setattr(attraction, key, value)
    db.session.commit()

    review_count = db.session.scalar(
        db.select(func.count(Feedback.id)).where(Feedback.attraction_id == attraction.id)
    )
    return jsonify(
        {"attraction": serialize_attraction(attraction, review_count=review_count)}
    )


@admin_bp.delete("/attractions/<int:attraction_id>")
@require_admin
def delete_attraction(attraction_id):
    """Delete an attraction. ORM cascades remove its interactions, feedback and
    itinerary items (users' trips silently lose this stop — acceptable for the
    admin catalogue tool)."""
    attraction = db.session.get(Attraction, attraction_id)
    if attraction is None:
        return json_error("Attraction not found.", 404)

    db.session.delete(attraction)
    db.session.commit()
    return jsonify({"deleted": attraction_id})


# ---------------------------------------------------------------------------
# Bulk actions
# ---------------------------------------------------------------------------

@admin_bp.post("/attractions/bulk-category")
@require_admin
def bulk_reassign_category():
    """Reassign ``category`` for many attractions at once.

    Body: ``{ ids: [int, ...], category: str }`` (blank/omitted category clears
    it). Returns ``{ updated: <n> }`` — the number of rows actually changed.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return json_error("Request body must be a JSON object.", 400)

    ids, error = parse_id_list(body.get("ids"))
    if error:
        return error

    category = body.get("category")
    if category is not None and not isinstance(category, str):
        return json_error("category must be a string.", 400)
    category = (category or "").strip() or None
    if category and len(category) > CATEGORY_MAX_LEN:
        return json_error(
            f"category must be at most {CATEGORY_MAX_LEN} characters.", 400
        )

    updated = (
        db.session.query(Attraction)
        .filter(Attraction.id.in_(ids))
        .update({Attraction.category: category}, synchronize_session=False)
    )
    db.session.commit()
    return jsonify({"updated": updated, "category": category})


@admin_bp.post("/attractions/bulk-delete")
@require_admin
def bulk_delete():
    """Delete many attractions at once. Body: ``{ ids: [int, ...] }``.

    Returns ``{ deleted: <n> }``. Deletes go through the ORM (one query per row)
    so the interaction/feedback/itinerary cascades fire, matching single delete.
    """
    body = request.get_json(silent=True)
    if not isinstance(body, dict):
        return json_error("Request body must be a JSON object.", 400)

    ids, error = parse_id_list(body.get("ids"))
    if error:
        return error

    attractions = db.session.scalars(
        db.select(Attraction).where(Attraction.id.in_(ids))
    ).all()
    for attraction in attractions:
        db.session.delete(attraction)
    db.session.commit()
    return jsonify({"deleted": len(attractions)})


# ---------------------------------------------------------------------------
# CSV import / export
# ---------------------------------------------------------------------------

@admin_bp.get("/attractions/export.csv")
@require_admin
def export_csv():
    """Download the whole catalogue as CSV (columns: see ``CSV_COLUMNS``)."""
    attractions = db.session.scalars(
        db.select(Attraction).order_by(Attraction.name.asc())
    ).all()

    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=CSV_COLUMNS, extrasaction="ignore")
    writer.writeheader()
    for a in attractions:
        writer.writerow(
            {
                "id": a.id,
                "name": a.name,
                "category": a.category or "",
                "description": a.description or "",
                "latitude": "" if a.latitude is None else a.latitude,
                "longitude": "" if a.longitude is None else a.longitude,
                "image_url": a.image_url or "",
            }
        )

    return Response(
        buffer.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=attractions.csv"},
    )


@admin_bp.post("/attractions/import")
@require_admin
def import_csv():
    """Bulk create/update attractions from an uploaded CSV.

    multipart/form-data with the file under field name ``file``. Recognised
    columns are ``CSV_COLUMNS``; ``name`` is required per row. A row with an
    ``id`` matching an existing attraction updates it; otherwise a new row is
    created. Each row is validated with the same rules as the single create/edit
    form. The whole import is one transaction: if any row is invalid nothing is
    committed and the offending rows are reported.

    Returns ``{ created, updated, errors: [{row, error}] }``.
    """
    file = request.files.get("file")
    if file is None or not file.filename:
        return json_error('A CSV file is required (multipart field name "file").', 400)

    try:
        text = file.read().decode("utf-8-sig")
    except UnicodeDecodeError:
        return json_error("CSV file must be UTF-8 encoded.", 400)

    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames or "name" not in {
        (h or "").strip().lower() for h in reader.fieldnames
    }:
        return json_error('CSV must have a header row including a "name" column.', 400)

    created = 0
    updated = 0
    errors = []
    pending = []  # (attraction_or_None_for_new, clean_fields)

    for index, raw in enumerate(reader, start=2):  # row 1 is the header
        if index - 1 > MAX_IMPORT_ROWS:
            return json_error(
                f"CSV has too many rows (max {MAX_IMPORT_ROWS}).", 400
            )
        # Normalise header casing/whitespace and drop empty cells → None.
        row = {
            (k or "").strip().lower(): (v.strip() if isinstance(v, str) else v)
            for k, v in raw.items()
        }
        body = {field: (row.get(field) or None) for field in CSV_COLUMNS if field != "id"}

        fields, error = validate_attraction_payload(body)
        if error:
            # error is (response, status); pull the message back out for the report.
            message = error[0].get_json().get("error", "invalid row")
            errors.append({"row": index, "error": message})
            continue

        target = None
        raw_id = (row.get("id") or "").strip()
        if raw_id:
            try:
                target = db.session.get(Attraction, int(raw_id))
            except ValueError:
                errors.append({"row": index, "error": "id must be an integer."})
                continue
            if target is None:
                errors.append({"row": index, "error": f"no attraction with id {raw_id}."})
                continue
        pending.append((target, fields))

    if errors:
        # All-or-nothing: don't half-apply a spreadsheet.
        return jsonify(
            {"created": 0, "updated": 0, "errors": errors, "committed": False}
        ), 400

    for target, fields in pending:
        if target is None:
            db.session.add(Attraction(**fields))
            created += 1
        else:
            for key, value in fields.items():
                setattr(target, key, value)
            updated += 1
    db.session.commit()

    return jsonify(
        {"created": created, "updated": updated, "errors": [], "committed": True}
    )


# ---------------------------------------------------------------------------
# Photo upload / serve
# ---------------------------------------------------------------------------

@admin_bp.post("/attractions/upload-image")
@require_admin
def upload_attraction_image():
    """Upload a photo from the admin's PC/phone storage for an attraction.

    multipart/form-data with the file under field name ``image`` (jpg / jpeg /
    png / webp; bodies over ``MAX_CONTENT_LENGTH`` are rejected with 413). Returns
    ``{image_url}`` — a relative path the frontend resolves against the API origin
    and stores as the attraction's ``image_url`` on save.
    """
    file = request.files.get("image")
    if file is None or not file.filename:
        return json_error(
            'An image file is required (multipart field name "image").', 400
        )

    ext = _image_extension(file.filename)
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        allowed = ", ".join(sorted(ALLOWED_IMAGE_EXTENSIONS))
        return json_error(f"Unsupported image type; use one of: {allowed}.", 400)

    filename = f"{uuid.uuid4().hex}.{ext}"
    upload_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], ATTRACTION_UPLOAD_SUBDIR
    )
    os.makedirs(upload_dir, exist_ok=True)
    file.save(os.path.join(upload_dir, filename))

    return jsonify({"image_url": f"/api/admin/attractions/uploads/{filename}"}), 201


@admin_bp.get("/attractions/uploads/<path:filename>")
def serve_attraction_upload(filename):
    """Serve a stored attraction photo so ``<img src>`` can render it.

    Deliberately unauthenticated: browsers can't attach the Firebase bearer token
    to image requests. Filenames are random 128-bit hex (unguessable), matching
    the approach in routes/images.py.
    """
    upload_dir = os.path.join(
        current_app.config["UPLOAD_FOLDER"], ATTRACTION_UPLOAD_SUBDIR
    )
    # send_from_directory guards against path traversal in ``filename``.
    return send_from_directory(upload_dir, filename)
