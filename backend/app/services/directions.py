"""Google Routes API integration with a simple in-memory TTL cache.

Given an ordered list of attraction coordinates for one itinerary day, this
computes the driving route through them and returns total distance/duration
plus per-leg figures between consecutive stops. We use the **Routes API**
(``computeRoutes``) rather than the legacy Directions API: Directions is
marked Legacy by Google (not enabled by default on new projects, no new
features), while Routes is the current product with the same waypoint
optimization capability (``optimizeWaypointOrder``) and lean responses via
field masks.

Results are cached per (ordered rounded coordinates, optimize flag) for
``ROUTE_CACHE_TTL`` seconds — the same idea as ``weather.py`` — so the
itinerary builder re-asking about an unchanged day order costs nothing.

Every failure (missing key, upstream down, rate limited, unreadable payload,
no route) raises :class:`DirectionsUnavailable` so the route handler can
answer with a single friendly 503 and the UI can degrade gracefully.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

import requests
from flask import current_app

_ROUTES_URL = "https://routes.googleapis.com/directions/v2:computeRoutes"

# Attraction coordinates are fixed points; rounding just normalises float noise
# so equivalent stop lists share one cache entry (~1 m precision).
_COORD_PRECISION = 5

# Keep the upstream call snappy — with caching this rarely runs, and we never
# want a slow routing API to blow the < 3s UX budget for a whole request.
_HTTP_TIMEOUT = 8  # seconds

# Fields we ask Routes API to return — anything not listed is omitted upstream,
# which keeps responses small. The optimized index is only meaningful (and only
# requested) when we ask for waypoint optimization.
_BASE_FIELD_MASK = (
    "routes.distanceMeters,routes.duration,"
    "routes.legs.distanceMeters,routes.legs.duration"
)
_OPTIMIZE_FIELD_MASK = _BASE_FIELD_MASK + ",routes.optimizedIntermediateWaypointIndex"

# key: (rounded (lat, lng) tuple, optimize flag) -> (fetched_at_epoch, payload)
_cache: dict[tuple, tuple[float, dict]] = {}
_cache_lock = threading.Lock()


class DirectionsUnavailable(Exception):
    """Raised when a route can't be computed (config or upstream fault)."""


def reset_cache():
    """Drop all cached entries. Used by tests to isolate cases."""
    with _cache_lock:
        _cache.clear()


def get_route(coords: list[tuple[float, float]], optimize: bool = False) -> dict:
    """Compute the driving route through ``coords`` (ordered, at least two).

    Returns::

        {
          "total_distance_m": int,
          "total_duration_s": int,
          "legs": [{"distance_m": int, "duration_s": int}, ...],
          "optimized_order": [int, ...] | None,   # see below
          "fetched_at": iso timestamp,
          "cached": bool,
        }

    With ``optimize=True`` the first and last stops stay fixed and Google is
    asked to reorder the middle ones to minimise travel; ``optimized_order``
    then lists indices into ``coords`` in the suggested visiting order (and
    totals/legs describe *that* order). Raises :class:`DirectionsUnavailable`
    on any failure.
    """
    if len(coords) < 2:
        raise ValueError("get_route needs at least two coordinates.")

    def round_point(p):
        if isinstance(p, str):
            return p
        return (round(p[0], _COORD_PRECISION), round(p[1], _COORD_PRECISION))

    rounded = tuple(round_point(p) for p in coords)
    key = (rounded, optimize)
    ttl = current_app.config.get("ROUTE_CACHE_TTL", 21600)

    with _cache_lock:
        hit = _cache.get(key)
        if hit and (time.time() - hit[0]) < ttl:
            return {**hit[1], "cached": True}

    payload = _build_payload(rounded, optimize)

    with _cache_lock:
        _cache[key] = (time.time(), payload)

    return {**payload, "cached": False}


def _build_payload(coords: tuple, optimize: bool) -> dict:
    api_key = current_app.config.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        raise DirectionsUnavailable("Route planning is not configured on the server.")

    def waypoint(point):
        if isinstance(point, str):
            return {"address": point}
        return {"location": {"latLng": {"latitude": point[0], "longitude": point[1]}}}

    intermediates = [waypoint(p) for p in coords[1:-1]]
    body = {
        "origin": waypoint(coords[0]),
        "destination": waypoint(coords[-1]),
        "travelMode": "DRIVE",
    }
    if intermediates:
        body["intermediates"] = intermediates
    # Only ask for reordering when there is something to reorder — with fewer
    # than two intermediates the current order is the only order.
    do_optimize = optimize and len(intermediates) >= 2
    if do_optimize:
        body["optimizeWaypointOrder"] = True

    headers = {
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": _OPTIMIZE_FIELD_MASK if do_optimize else _BASE_FIELD_MASK,
    }
    data = _post_json(body, headers)

    routes = data.get("routes") or []
    if not routes:
        raise DirectionsUnavailable("No route could be found between these stops.")
    route = routes[0]

    legs = [
        {
            "distance_m": leg.get("distanceMeters") or 0,
            "duration_s": _seconds(leg.get("duration")),
        }
        for leg in route.get("legs") or []
    ]
    if not legs:
        raise DirectionsUnavailable("Routing service sent an unreadable response.")

    optimized_order = None
    if optimize:
        if do_optimize:
            index = route.get("optimizedIntermediateWaypointIndex")
            if index is None or len(index) != len(intermediates):
                raise DirectionsUnavailable(
                    "Routing service sent an unreadable response."
                )
            optimized_order = [0, *(i + 1 for i in index), len(coords) - 1]
        else:
            optimized_order = list(range(len(coords)))  # nothing to reorder

    return {
        "total_distance_m": route.get("distanceMeters")
        or sum(leg["distance_m"] for leg in legs),
        "total_duration_s": _seconds(route.get("duration"))
        or sum(leg["duration_s"] for leg in legs),
        "legs": legs,
        "optimized_order": optimized_order,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _post_json(body: dict, headers: dict) -> dict:
    """POST to the Routes API and return parsed JSON, or raise
    :class:`DirectionsUnavailable`."""
    try:
        resp = requests.post(
            _ROUTES_URL, json=body, headers=headers, timeout=_HTTP_TIMEOUT
        )
    except requests.RequestException as exc:
        raise DirectionsUnavailable("Could not reach the routing service.") from exc

    if resp.status_code == 429:
        raise DirectionsUnavailable("Routing service is rate limited — try again shortly.")
    if resp.status_code != 200:
        raise DirectionsUnavailable("Routing service returned an error.")

    try:
        return resp.json()
    except ValueError as exc:
        raise DirectionsUnavailable("Routing service sent an unreadable response.") from exc


def _seconds(value) -> int:
    """Parse a Routes API duration like ``\"12600s\"`` into whole seconds."""
    if isinstance(value, str) and value.endswith("s"):
        try:
            return int(float(value[:-1]))
        except ValueError:
            pass
    return 0
