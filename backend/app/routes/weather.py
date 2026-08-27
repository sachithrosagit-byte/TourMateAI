"""Weather proxy endpoint.

``GET /api/weather/<lat>/<lng>`` returns current conditions plus a short daily
forecast for a coordinate, proxied from OpenWeather and cached server-side (see
``services/weather.py``). The frontend uses it for the itinerary planner's
per-day weather widgets and weather-aware suggestions.

Any upstream/config failure comes back as a single friendly 503 with
``{"error": ..., "available": false}`` so the UI can degrade gracefully rather
than break. Coordinates are taken from the path (they may be negative), so this
parses/validates them by hand instead of relying on Flask's ``float`` converter.
"""

from flask import Blueprint, jsonify

from ..services.weather import WeatherUnavailable, get_weather
from .helpers import json_error

weather_bp = Blueprint("weather", __name__)


@weather_bp.get("/weather/<lat>/<lng>")
def weather(lat, lng):
    try:
        lat_f = float(lat)
        lng_f = float(lng)
    except (TypeError, ValueError):
        return json_error("lat and lng must be numbers.", 400)

    if not (-90.0 <= lat_f <= 90.0) or not (-180.0 <= lng_f <= 180.0):
        return json_error("lat/lng are out of range.", 400)

    try:
        data = get_weather(lat_f, lng_f)
    except WeatherUnavailable as exc:
        # One friendly shape for every fault; the frontend falls back on it.
        return jsonify({"error": str(exc), "available": False}), 503

    data["available"] = True
    return jsonify(data)
