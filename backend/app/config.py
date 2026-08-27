"""Environment-driven Flask configuration.

Loads a repo-root `.env` (and an optional `backend/.env` override), then builds
the SQLAlchemy MySQL connection URI from the `DB_*` variables documented in
`.env.example`.
"""

import os
from pathlib import Path
from urllib.parse import quote_plus

from dotenv import load_dotenv

_BACKEND_DIR = Path(__file__).resolve().parents[1]   # backend/
_REPO_ROOT = _BACKEND_DIR.parent                     # repo root

# Repo-root .env first, then backend/.env (the latter overrides if present).
load_dotenv(_REPO_ROOT / ".env")
load_dotenv(_BACKEND_DIR / ".env", override=True)


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "change-me")

    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASSWORD = os.environ.get("DB_PASSWORD", "")
    DB_HOST = os.environ.get("DB_HOST", "localhost")
    DB_PORT = os.environ.get("DB_PORT", "3306")
    DB_NAME = os.environ.get("DB_NAME", "tourmateai")

    # quote_plus so passwords with special characters don't corrupt the URI.
    SQLALCHEMY_DATABASE_URI = (
        os.environ.get("DATABASE_URL")
        or f"mysql+pymysql://{DB_USER}:{quote_plus(DB_PASSWORD)}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Where user-uploaded images (landmark recognition) are stored. Local disk
    # for the prototype; swap for cloud storage by changing this + the serving
    # route in routes/images.py.
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER") or str(_BACKEND_DIR / "uploads")

    # Reject request bodies over this size (Flask returns 413 — handled as JSON
    # in the app factory). Generous enough for phone photos.
    MAX_CONTENT_LENGTH = 8 * 1024 * 1024  # 8 MB

    # ===== External API keys =====
    # OpenWeather backs the /api/weather proxy; Google Maps is consumed by the
    # frontend (VITE_GOOGLE_MAPS_API_KEY) but kept here too for any server-side use.
    OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY", "")
    GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY", "")

    # How long (seconds) a fetched weather result is reused before refetching —
    # keeps us comfortably inside the OpenWeather free-tier rate limit. 30 min.
    WEATHER_CACHE_TTL = int(os.environ.get("WEATHER_CACHE_TTL", "1800"))

    # Same idea for computed day routes (Google Routes API). Distances between
    # fixed attractions barely change, so 6 h keeps free-tier usage minimal.
    ROUTE_CACHE_TTL = int(os.environ.get("ROUTE_CACHE_TTL", "21600"))

    # Route the AI features (recommend / chat / identify) to the mock stand-ins in
    # services/ai_service.py (True) or the teammate's real AI modules (False).
    # Keep True until those modules — and the `_real_*` branches — are wired up.
    USE_MOCK_AI = os.environ.get("USE_MOCK_AI", "true").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
