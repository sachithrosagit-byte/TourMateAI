"""Itinerary endpoints — trip plans and their day-by-day items.

An itinerary is a titled trip with optional start/end dates; its items are
attractions pinned to a day (``day_number``, 1-based) in a user-chosen order
(``order_index``). The planner UI groups items by day, so every read returns
items already sorted by (day_number, order_index) — the model's relationship
ordering guarantees that.

All routes operate on the **current user's** itineraries only; asking for
someone else's (or a missing) itinerary is a plain 404 so ids don't leak.

Routes (registered under ``/api``):
  - ``GET    /api/itineraries``                     auth: my itineraries, newest first
  - ``POST   /api/itineraries``                     auth: create a trip
  - ``GET    /api/itineraries/<id>``                auth: one trip, items included
  - ``PUT    /api/itineraries/<id>``                auth: update title/dates
  - ``DELETE /api/itineraries/<id>``                auth: delete trip + items
  - ``POST   /api/itineraries/<id>/items``          auth: add an attraction to a day
  - ``PUT    /api/itineraries/<id>/items/reorder``  auth: reorder one day's items
  - ``DELETE /api/itineraries/<id>/items/<item_id>`` auth: remove an item
  - ``GET    /api/itineraries/<id>/days/<day>/route`` auth: driving route for a day
"""

from datetime import date
import json

from flask import Blueprint, g, jsonify, request

from ..extensions import db
from ..models import Attraction, Itinerary, ItineraryItem, Hotel
from ..services.directions import DirectionsUnavailable, get_route
from .attractions import _serialize_attraction
from .auth import require_auth
from .helpers import json_error

itineraries_bp = Blueprint("itineraries", __name__)

# How many attraction names to include as a per-itinerary teaser.
PREVIEW_STOPS = 3

MAX_TITLE_LENGTH = 200
MAX_TRIP_DAYS = 60  # sanity cap; nobody plans a 200-day trip in this UI


def _serialize_itinerary(itinerary):
    """Shape an Itinerary for JSON list views.

    Carries an item count + first few attraction names so the Dashboard can
    render a meaningful card without a second round-trip per itinerary.
    ``items`` is already ordered by (day_number, order_index) — see the model.
    """
    stops = []
    for item in itinerary.items[:PREVIEW_STOPS]:
        if item.attraction:
            stops.append(item.attraction.name)
        elif item.hotel:
            stops.append(item.hotel.name)
    return {
        "id": itinerary.id,
        "title": itinerary.title,
        "description": itinerary.description,
        "start_location": itinerary.start_location,
        "end_location": itinerary.end_location,
        "stops": json.loads(itinerary.stops) if itinerary.stops else [],
        "start_date": itinerary.start_date.isoformat() if itinerary.start_date else None,
        "end_date": itinerary.end_date.isoformat() if itinerary.end_date else None,
        "trip_type": itinerary.trip_type,
        "created_at": itinerary.created_at.isoformat() if itinerary.created_at else None,
        "item_count": len(itinerary.items),
        "preview_stops": stops,
        "is_ai_generated": itinerary.is_ai_generated,
    }


def _serialize_item(item):
    """Shape an ItineraryItem for JSON, attraction/hotel expanded for direct render."""
    return {
        "id": item.id,
        "attraction_id": item.attraction_id,
        "hotel_id": item.hotel_id,
        "day_number": item.day_number,
        "order_index": item.order_index,
        "notes": item.notes,
        "attraction": _serialize_attraction(item.attraction) if item.attraction else None,
        "hotel": item.hotel.to_dict() if item.hotel else None,
    }


def _serialize_itinerary_detail(itinerary):
    """List shape + the full ordered item list (the Builder page's payload)."""
    data = _serialize_itinerary(itinerary)
    data["items"] = [_serialize_item(item) for item in itinerary.items]
    return data


def _get_owned_itinerary(itinerary_id):
    """The current user's itinerary by id, or None (missing OR not theirs)."""
    return Itinerary.query.filter_by(
        id=itinerary_id, user_id=g.current_user.id
    ).first()


def _day_count(itinerary):
    """Days in the trip, or None when either date is missing."""
    if itinerary.start_date and itinerary.end_date:
        return (itinerary.end_date - itinerary.start_date).days + 1
    return None


def _parse_date_field(body, field):
    """Read an optional ISO ``YYYY-MM-DD`` date from the JSON body.

    Returns ``(provided, value, error)`` — ``provided`` distinguishes "field
    absent" from an explicit ``null`` (which clears the date).
    """
    if field not in body:
        return False, None, None
    raw = body[field]
    if raw is None:
        return True, None, None
    if isinstance(raw, str):
        try:
            return True, date.fromisoformat(raw), None
        except ValueError:
            pass
    return True, None, json_error(f"{field} must be a YYYY-MM-DD date.", 400)


def _validate_dates(start, end):
    """Cross-field date rules shared by create + update. Returns an error or None."""
    if start and end:
        if end < start:
            return json_error("end_date cannot be before start_date.", 400)
        if (end - start).days + 1 > MAX_TRIP_DAYS:
            return json_error(f"Trips are capped at {MAX_TRIP_DAYS} days.", 400)
    return None


def _clean_title(raw):
    """Validated trip title or ``(None, error)``."""
    if not isinstance(raw, str) or not raw.strip():
        return None, json_error("title is required and must be a non-empty string.", 400)
    title = raw.strip()
    if len(title) > MAX_TITLE_LENGTH:
        return None, json_error(
            f"title must be at most {MAX_TITLE_LENGTH} characters.", 400
        )
    return title, None


# =============================================================================
# Itineraries
# =============================================================================

@itineraries_bp.get("/itineraries")
@require_auth
def list_itineraries():
    """Return the current user's itineraries, newest first."""
    rows = (
        Itinerary.query.filter_by(user_id=g.current_user.id)
        .order_by(Itinerary.created_at.desc())
        .all()
    )
    return jsonify({"itineraries": [_serialize_itinerary(i) for i in rows]})


@itineraries_bp.post("/itineraries")
@require_auth
def create_itinerary():
    """Create a trip. Body: ``title`` (required), ``start_date``/``end_date``
    (optional ISO dates; when both present, end >= start)."""
    body = request.get_json(silent=True) or {}

    title, error = _clean_title(body.get("title"))
    if error:
        return error
        
    description = body.get("description")
    if description is not None and not isinstance(description, str):
        return json_error("description must be a string.", 400)
        
    start_location = body.get("start_location")
    end_location = body.get("end_location")
    
    stops_input = body.get("stops", [])
    if not isinstance(stops_input, list):
        return json_error("stops must be a list.", 400)
    stops_json = json.dumps(stops_input) if stops_input else None

    _, start, error = _parse_date_field(body, "start_date")
    if error:
        return error
    _, end, error = _parse_date_field(body, "end_date")
    if error:
        return error
    error = _validate_dates(start, end)
    if error:
        return error

    is_ai_generated = bool(body.get("is_ai_generated", False))
    trip_type = body.get("trip_type", "Solo")

    itinerary = Itinerary(
        user_id=g.current_user.id, 
        title=title, 
        description=description, 
        start_location=start_location,
        end_location=end_location,
        stops=stops_json,
        start_date=start, 
        end_date=end,
        trip_type=trip_type,
        is_ai_generated=is_ai_generated
    )
    db.session.add(itinerary)
    db.session.commit()
    return jsonify({"itinerary": _serialize_itinerary_detail(itinerary)}), 201


@itineraries_bp.get("/itineraries/<int:itinerary_id>")
@require_auth
def get_itinerary(itinerary_id):
    """One itinerary with its full ordered item list."""
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)
    return jsonify({"itinerary": _serialize_itinerary_detail(itinerary)})


@itineraries_bp.put("/itineraries/<int:itinerary_id>")
@require_auth
def update_itinerary(itinerary_id):
    """Update title and/or dates. Only fields present in the body change;
    an explicit ``null`` clears a date.

    If the new dates shrink the trip, items stranded past the last day are
    pulled onto the final day (appended after its existing items) rather than
    silently orphaned.
    """
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)

    body = request.get_json(silent=True) or {}

    if "title" in body:
        title, error = _clean_title(body.get("title"))
        if error:
            return error
        itinerary.title = title

    if "trip_type" in body:
        itinerary.trip_type = body.get("trip_type")

    start_given, start, error = _parse_date_field(body, "start_date")
    if error:
        return error
    end_given, end, error = _parse_date_field(body, "end_date")
    if error:
        return error

    new_start = start if start_given else itinerary.start_date
    new_end = end if end_given else itinerary.end_date
    error = _validate_dates(new_start, new_end)
    if error:
        return error
    itinerary.start_date = new_start
    itinerary.end_date = new_end

    days = _day_count(itinerary)
    if days is not None:
        stranded = [
            item for item in itinerary.items
            if item.day_number and item.day_number > days
        ]
        if stranded:
            tail = max(
                (i.order_index or 0 for i in itinerary.items
                 if i.day_number == days),
                default=-1,
            )
            for offset, item in enumerate(stranded, start=1):
                item.day_number = days
                item.order_index = tail + offset

    db.session.commit()
    return jsonify({"itinerary": _serialize_itinerary_detail(itinerary)})


@itineraries_bp.delete("/itineraries/<int:itinerary_id>")
@require_auth
def delete_itinerary(itinerary_id):
    """Delete a trip; its items go with it (cascade)."""
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)
    db.session.delete(itinerary)
    db.session.commit()
    return jsonify({"deleted": itinerary_id})


# =============================================================================
# Items
# =============================================================================

@itineraries_bp.post("/itineraries/<int:itinerary_id>/items")
@require_auth
def add_item(itinerary_id):
    """Add an attraction to a day. Body: ``attraction_id``, ``day_number``
    (1-based; must fit inside the trip's dates when those are set). The item
    lands at the end of that day."""
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)

    body = request.get_json(silent=True) or {}

    attraction_id = body.get("attraction_id")
    hotel_id = body.get("hotel_id")
    
    if attraction_id is None and hotel_id is None:
        return json_error("Either attraction_id or hotel_id is required.", 400)
    if attraction_id is not None and hotel_id is not None:
        return json_error("Cannot set both attraction_id and hotel_id on the same item.", 400)

    if attraction_id is not None:
        if not isinstance(attraction_id, int):
            return json_error("attraction_id must be an integer.", 400)
        attraction = db.session.get(Attraction, attraction_id)
        if not attraction:
            return json_error("Attraction not found.", 404)
            
    if hotel_id is not None:
        if not isinstance(hotel_id, int):
            return json_error("hotel_id must be an integer.", 400)
        hotel = db.session.get(Hotel, hotel_id)
        if not hotel:
            return json_error("Hotel not found.", 404)

    day_number = body.get("day_number")
    if not isinstance(day_number, int) or day_number < 1:
        return json_error("day_number is required and must be a positive integer.", 400)
    days = _day_count(itinerary)
    if days is not None and day_number > days:
        return json_error(f"day_number is outside this trip ({days} days).", 400)

    tail = max(
        (i.order_index or 0 for i in itinerary.items if i.day_number == day_number),
        default=-1,
    )
    item = ItineraryItem(
        itinerary_id=itinerary.id,
        attraction_id=attraction_id,
        hotel_id=hotel_id,
        day_number=day_number,
        order_index=tail + 1,
    )
    db.session.add(item)
    db.session.commit()
    return jsonify({"item": _serialize_item(item)}), 201


@itineraries_bp.put("/itineraries/<int:itinerary_id>/items/reorder")
@require_auth
def reorder_items(itinerary_id):
    """Set one day's item order. Body: ``day_number``, ``item_ids`` — the
    complete new order for that day. Every id must belong to this itinerary;
    listed items are (re)assigned to the day, so this also moves an item in
    from another day when the client allows cross-day drags."""
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)

    body = request.get_json(silent=True) or {}

    day_number = body.get("day_number")
    if not isinstance(day_number, int) or day_number < 1:
        return json_error("day_number is required and must be a positive integer.", 400)

    item_ids = body.get("item_ids")
    if not isinstance(item_ids, list) or not all(
        isinstance(i, int) for i in item_ids
    ):
        return json_error("item_ids must be a list of integers.", 400)
    if len(set(item_ids)) != len(item_ids):
        return json_error("item_ids contains duplicates.", 400)

    by_id = {item.id: item for item in itinerary.items}
    unknown = [i for i in item_ids if i not in by_id]
    if unknown:
        return json_error(f"Items not in this itinerary: {unknown}.", 400)

    for position, item_id in enumerate(item_ids):
        by_id[item_id].day_number = day_number
        by_id[item_id].order_index = position

    db.session.commit()
    # Session state is current; re-serialize through a fresh ordered read.
    db.session.refresh(itinerary)
    return jsonify({"itinerary": _serialize_itinerary_detail(itinerary)})


@itineraries_bp.delete("/itineraries/<int:itinerary_id>/items/<int:item_id>")
@require_auth
def remove_item(itinerary_id, item_id):
    """Remove one item from the trip."""
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)

    item = next((i for i in itinerary.items if i.id == item_id), None)
    if not item:
        return json_error("Item not found in this itinerary.", 404)

    db.session.delete(item)
    db.session.commit()
    return jsonify({"deleted": item_id})


# =============================================================================
# Day route (Google Routes API, via services/directions.py)
# =============================================================================

@itineraries_bp.get("/itineraries/<int:itinerary_id>/days/<int:day_number>/route")
@require_auth
def day_route(itinerary_id, day_number):
    """Driving route through one day's stops, in their current order.

    Only items whose attraction has coordinates count as stops; a day needs at
    least two of them to have a route. With ``?optimize=true`` the response
    also carries ``suggested_item_order`` — the day's located item ids in the
    travel-minimising order Google suggests (first and last stops stay fixed),
    with the route totals describing that suggested order. The suggestion is
    never applied here; the client asks the user and uses the reorder endpoint.

    Upstream/config failures come back as a friendly 503 with
    ``{"error": ..., "available": false}``, mirroring the weather route.
    """
    itinerary = _get_owned_itinerary(itinerary_id)
    if not itinerary:
        return json_error("Itinerary not found.", 404)

    valid_items = []
    for item in itinerary.items:
        if item.attraction and item.attraction.latitude is not None and item.attraction.longitude is not None:
            valid_items.append(item)
        elif item.hotel and item.hotel.latitude is not None and item.hotel.longitude is not None:
            valid_items.append(item)
    
    if not valid_items:
        return json_error("This itinerary has no valid stops to route.", 400)

    total_days = max(item.day_number for item in valid_items)
    
    stops = [item for item in valid_items if item.day_number == day_number]

    coords = []
    for s in stops:
        if s.attraction:
            coords.append((s.attraction.latitude, s.attraction.longitude))
        elif s.hotel:
            coords.append((s.hotel.latitude, s.hotel.longitude))

    response_stops = []
    for s in stops:
        response_stops.append({
            "item_id": s.id,
            "attraction_id": s.attraction_id,
            "hotel_id": s.hotel_id,
            "name": s.attraction.name if s.attraction else s.hotel.name,
            "day_number": s.day_number,
        })

    if day_number == 1 and itinerary.start_location:
        coords.insert(0, itinerary.start_location)
        response_stops.insert(0, {
            "item_id": "start_location",
            "attraction_id": None,
            "name": f"Start: {itinerary.start_location}",
            "day_number": 1,
        })
    elif day_number > 1:
        prev_items = [item for item in valid_items if item.day_number < day_number]
        if prev_items:
            prev_last = prev_items[-1]
            if prev_last.attraction:
                coords.insert(0, (prev_last.attraction.latitude, prev_last.attraction.longitude))
                prev_name = prev_last.attraction.name
            else:
                coords.insert(0, (prev_last.hotel.latitude, prev_last.hotel.longitude))
                prev_name = prev_last.hotel.name

            response_stops.insert(0, {
                "item_id": prev_last.id,
                "attraction_id": prev_last.attraction_id,
                "hotel_id": prev_last.hotel_id,
                "name": prev_name,
                "day_number": prev_last.day_number,
            })

    if day_number == total_days and total_days > 1:
        if itinerary.start_location:
            coords.append(itinerary.start_location)
            response_stops.append({
                "item_id": "start_location",
                "attraction_id": None,
                "name": f"Start: {itinerary.start_location}",
                "day_number": total_days,
            })
        else:
            first_overall = valid_items[0]
            if not stops or stops[-1].id != first_overall.id:
                if first_overall.attraction:
                    coords.append((first_overall.attraction.latitude, first_overall.attraction.longitude))
                    first_name = first_overall.attraction.name
                else:
                    coords.append((first_overall.hotel.latitude, first_overall.hotel.longitude))
                    first_name = first_overall.hotel.name

                response_stops.append({
                    "item_id": first_overall.id,
                    "attraction_id": first_overall.attraction_id,
                    "hotel_id": first_overall.hotel_id,
                    "name": first_name,
                    "day_number": first_overall.day_number,
                })

    if len(coords) < 2:
        return json_error(
            "This day needs at least two stops with map locations to route.", 400
        )

    optimize = (request.args.get("optimize") or "").strip().lower() in (
        "1", "true", "yes", "on",
    )

    try:
        route = get_route(coords, optimize=optimize)
    except DirectionsUnavailable as exc:
        # One friendly shape for every fault; the frontend falls back on it.
        return jsonify({"error": str(exc), "available": False}), 503

    optimized_order = route.pop("optimized_order", None)
    response = {
        "available": True,
        "day_number": day_number,
        "stops": response_stops,
        "route": route,
    }
    if optimized_order is not None:
        response["suggested_item_order"] = [
            response_stops[i]["item_id"]
            for i in optimized_order
            if response_stops[i]["day_number"] == day_number
            and isinstance(response_stops[i]["item_id"], int)
        ]
    return jsonify(response)
