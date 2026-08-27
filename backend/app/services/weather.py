"""OpenWeather integration with a simple in-memory TTL cache.

The frontend asks for weather by coordinate (an attraction's lat/lng). We proxy
that to the OpenWeather 2.5 *current* + *5-day / 3-hour forecast* endpoints (both
on the free tier), normalise the two payloads into one lean shape, and cache the
result per rounded coordinate for ``WEATHER_CACHE_TTL`` seconds. Caching means
repeated views of the same place — and the itinerary planner asking about several
days that start at the same location — don't burn through the free-tier limit.

Every failure (missing key, upstream down, rate limited, unreadable payload)
raises :class:`WeatherUnavailable` so the route can answer with a single friendly
503 and the UI can fall back gracefully instead of rendering a broken widget.
"""

from __future__ import annotations

import threading
import time
from datetime import datetime, timezone

import requests
from flask import current_app

_CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
_FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"

# OpenWeather "main" groups we treat as "bad" — the ones that put outdoor plans
# at risk and should raise a warning badge on an itinerary day.
_BAD_CONDITIONS = {"Rain", "Thunderstorm", "Drizzle", "Snow", "Squall", "Tornado"}

# Round coordinates to ~1 km so nearby attractions share one cache entry.
_COORD_PRECISION = 2

# Keep the upstream call snappy — with caching this rarely runs, and we never
# want a slow weather API to blow the < 3s UX budget for a whole request.
_HTTP_TIMEOUT = 6  # seconds

# key: (lat, lng) rounded -> (fetched_at_epoch, payload)
_cache: dict[tuple[float, float], tuple[float, dict]] = {}
_cache_lock = threading.Lock()


class WeatherUnavailable(Exception):
    """Raised when a weather payload can't be produced (config or upstream fault)."""


def reset_cache():
    """Drop all cached entries. Used by tests to isolate cases."""
    with _cache_lock:
        _cache.clear()


def get_weather(lat: float, lng: float) -> dict:
    """Return normalised current + forecast weather for a coordinate.

    Serves a fresh cached result when one exists, otherwise fetches, caches and
    returns. Raises :class:`WeatherUnavailable` on any failure.
    """
    key = (round(lat, _COORD_PRECISION), round(lng, _COORD_PRECISION))
    ttl = current_app.config.get("WEATHER_CACHE_TTL", 1800)

    with _cache_lock:
        hit = _cache.get(key)
        if hit and (time.time() - hit[0]) < ttl:
            return {**hit[1], "cached": True}

    payload = _build_payload(key[0], key[1])

    with _cache_lock:
        _cache[key] = (time.time(), payload)

    return {**payload, "cached": False}


def _build_payload(lat: float, lng: float) -> dict:
    api_key = current_app.config.get("OPENWEATHER_API_KEY")
    if not api_key:
        raise WeatherUnavailable("Weather is not configured on the server.")

    params = {"lat": lat, "lon": lng, "units": "metric", "appid": api_key}
    current = _fetch_json(_CURRENT_URL, params)
    forecast = _fetch_json(_FORECAST_URL, params)

    return {
        "location": {"lat": lat, "lng": lng},
        "current": _normalise_current(current),
        "forecast": _summarise_forecast(forecast),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
    }


def _fetch_json(url: str, params: dict) -> dict:
    """GET ``url`` and return parsed JSON, or raise :class:`WeatherUnavailable`."""
    try:
        resp = requests.get(url, params=params, timeout=_HTTP_TIMEOUT)
    except requests.RequestException as exc:
        raise WeatherUnavailable("Could not reach the weather service.") from exc

    if resp.status_code == 429:
        raise WeatherUnavailable("Weather service is rate limited — try again shortly.")
    if resp.status_code != 200:
        raise WeatherUnavailable("Weather service returned an error.")

    try:
        return resp.json()
    except ValueError as exc:
        raise WeatherUnavailable("Weather service sent an unreadable response.") from exc


def _weather_block(entry: dict) -> tuple[str, str, str]:
    """Pull (condition, description, icon) out of an OpenWeather entry."""
    weather = (entry.get("weather") or [{}])[0]
    return (
        weather.get("main") or "Unknown",
        weather.get("description") or "",
        weather.get("icon") or "",
    )


def _normalise_current(data: dict) -> dict:
    condition, description, icon = _weather_block(data)
    main = data.get("main") or {}
    wind = data.get("wind") or {}
    wind_ms = wind.get("speed")
    return {
        "temp_c": _round1(main.get("temp")),
        "feels_like_c": _round1(main.get("feels_like")),
        "humidity": main.get("humidity"),
        "wind_kmh": _round1(wind_ms * 3.6) if wind_ms is not None else None,
        "condition": condition,
        "description": description,
        "icon": icon,
        "is_bad": condition in _BAD_CONDITIONS,
    }


def _summarise_forecast(data: dict) -> list[dict]:
    """Collapse the 3-hourly forecast list into one summary per calendar day.

    Temps become the day's min/max across its slices. A day is flagged ``is_bad``
    if *any* slice is bad (rain often shows in only part of the day). The
    representative condition/icon is the first bad slice when the day is bad, else
    the slice nearest midday — so the chip reflects what a traveler would plan for.
    ``rain_chance`` is the worst slice's precipitation probability as a percent.
    """
    days: dict[str, dict] = {}

    for entry in data.get("list", []):
        stamp = entry.get("dt_txt")  # e.g. "2026-07-08 12:00:00"
        if not stamp or " " not in stamp:
            continue
        date_part, time_part = stamp.split(" ", 1)
        condition, description, icon = _weather_block(entry)
        temp = (entry.get("main") or {}).get("temp")
        pop = entry.get("pop")  # probability of precipitation, 0..1

        bucket = days.setdefault(
            date_part,
            {"temp_min": None, "temp_max": None, "bad_rep": None,
             "noon_rep": None, "noon_dist": 99, "pop_max": None},
        )

        if temp is not None:
            lo, hi = bucket["temp_min"], bucket["temp_max"]
            bucket["temp_min"] = temp if lo is None else min(lo, temp)
            bucket["temp_max"] = temp if hi is None else max(hi, temp)

        if pop is not None:
            prev = bucket["pop_max"]
            bucket["pop_max"] = pop if prev is None else max(prev, pop)

        block = (condition, description, icon)
        if condition in _BAD_CONDITIONS and bucket["bad_rep"] is None:
            bucket["bad_rep"] = block

        try:
            dist = abs(int(time_part[:2]) - 12)
        except ValueError:
            dist = 99
        if dist < bucket["noon_dist"]:
            bucket["noon_dist"] = dist
            bucket["noon_rep"] = block

    result = []
    for date_part in sorted(days):
        bucket = days[date_part]
        rep = bucket["bad_rep"] or bucket["noon_rep"] or ("Unknown", "", "")
        condition, description, icon = rep
        pop_max = bucket["pop_max"]
        result.append(
            {
                "date": date_part,
                "temp_min_c": _round1(bucket["temp_min"]),
                "temp_max_c": _round1(bucket["temp_max"]),
                "condition": condition,
                "description": description,
                "icon": icon,
                "is_bad": bucket["bad_rep"] is not None,
                "rain_chance": round(pop_max * 100) if pop_max is not None else None,
            }
        )
    return result


def _round1(value):
    return round(float(value), 1) if value is not None else None
