"""Tests for the weather proxy endpoint + its normalisation/caching.

The OpenWeather HTTP calls are stubbed at ``services.weather._fetch_json`` so no
network (or real API key) is needed; we drive the two endpoints by URL.
"""

import pytest

import app.services.weather as weather_service

# --- Canned OpenWeather payloads -------------------------------------------

_CURRENT = {
    "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}],
    "main": {"temp": 29.44, "feels_like": 31.0, "humidity": 74},
    "wind": {"speed": 5.0},  # m/s → 18 km/h
}

# Two days: 08 Jul is dry (clear/clouds), 09 Jul has a rainy afternoon slice.
_FORECAST = {
    "list": [
        {"dt_txt": "2026-07-08 09:00:00", "main": {"temp": 27.0}, "pop": 0.0,
         "weather": [{"main": "Clouds", "description": "few clouds", "icon": "02d"}]},
        {"dt_txt": "2026-07-08 12:00:00", "main": {"temp": 31.0}, "pop": 0.1,
         "weather": [{"main": "Clear", "description": "clear sky", "icon": "01d"}]},
        {"dt_txt": "2026-07-09 12:00:00", "main": {"temp": 28.0}, "pop": 0.35,
         "weather": [{"main": "Clouds", "description": "scattered clouds", "icon": "03d"}]},
        {"dt_txt": "2026-07-09 15:00:00", "main": {"temp": 26.0}, "pop": 0.8,
         "weather": [{"main": "Rain", "description": "moderate rain", "icon": "10d"}]},
    ]
}


def _stub_fetch(monkeypatch, calls=None):
    """Route _fetch_json to canned data by URL; optionally count invocations."""
    def fake(url, params):
        if calls is not None:
            calls.append(url)
        return _CURRENT if "weather" in url and "forecast" not in url else _FORECAST

    monkeypatch.setattr(weather_service, "_fetch_json", fake)


@pytest.fixture(autouse=True)
def _fresh_cache_and_key(app):
    """Isolate the module cache and give the app a (fake) key for each test."""
    weather_service.reset_cache()
    app.config["OPENWEATHER_API_KEY"] = "test-key"
    yield
    weather_service.reset_cache()


# --- Success + normalisation ------------------------------------------------

def test_returns_current_and_daily_forecast(client, monkeypatch):
    _stub_fetch(monkeypatch)
    r = client.get("/api/weather/7.957/80.76")
    assert r.status_code == 200
    body = r.get_json()

    assert body["available"] is True
    assert body["current"]["condition"] == "Clear"
    assert body["current"]["is_bad"] is False
    assert body["current"]["temp_c"] == 29.4  # rounded to 1dp
    assert body["current"]["humidity"] == 74
    assert body["current"]["wind_kmh"] == 18.0  # 5 m/s converted

    # One summary per calendar day, sorted.
    dates = [d["date"] for d in body["forecast"]]
    assert dates == ["2026-07-08", "2026-07-09"]


def test_bad_weather_day_is_flagged_with_min_max(client, monkeypatch):
    _stub_fetch(monkeypatch)
    body = client.get("/api/weather/7.957/80.76").get_json()
    by_date = {d["date"]: d for d in body["forecast"]}

    dry = by_date["2026-07-08"]
    assert dry["is_bad"] is False
    assert dry["temp_min_c"] == 27.0 and dry["temp_max_c"] == 31.0
    assert dry["rain_chance"] == 10  # worst slice pop as a percent

    rainy = by_date["2026-07-09"]
    assert rainy["is_bad"] is True          # afternoon rain flags the whole day
    assert rainy["condition"] == "Rain"      # bad slice is the representative one
    assert rainy["rain_chance"] == 80


# --- Caching ----------------------------------------------------------------

def test_second_call_is_served_from_cache(client, monkeypatch):
    calls = []
    _stub_fetch(monkeypatch, calls)

    first = client.get("/api/weather/7.957/80.76").get_json()
    assert first["cached"] is False
    assert len(calls) == 2  # current + forecast

    second = client.get("/api/weather/7.957/80.76").get_json()
    assert second["cached"] is True
    assert len(calls) == 2  # no refetch — same rounded coordinate


# --- Failure handling -------------------------------------------------------

def test_upstream_failure_returns_friendly_503(client, monkeypatch):
    def boom(url, params):
        raise weather_service.WeatherUnavailable("Could not reach the weather service.")

    monkeypatch.setattr(weather_service, "_fetch_json", boom)
    r = client.get("/api/weather/7.957/80.76")
    assert r.status_code == 503
    body = r.get_json()
    assert body["available"] is False
    assert "error" in body


def test_missing_api_key_returns_503(client, monkeypatch, app):
    app.config["OPENWEATHER_API_KEY"] = ""
    _stub_fetch(monkeypatch)  # never reached — key check happens first
    r = client.get("/api/weather/7.957/80.76")
    assert r.status_code == 503
    assert r.get_json()["available"] is False


# --- Input validation -------------------------------------------------------

def test_non_numeric_coords_return_400(client):
    assert client.get("/api/weather/abc/def").status_code == 400


def test_out_of_range_coords_return_400(client):
    assert client.get("/api/weather/200/0").status_code == 400
    assert client.get("/api/weather/0/999").status_code == 400
