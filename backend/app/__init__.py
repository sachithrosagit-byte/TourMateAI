"""Flask application factory.

Creates the app, loads config, initialises the database + migrations, and mounts
blueprints. The AI package (`app.ai`) is mounted at `/api/ai/*` and stays behind
the JSON contracts in docs/api-contract.md — do not reach across that boundary.

Note: config/models/migrations here are the Web dev's area (built on their behalf
while they were unavailable — see backend/README.md ownership map).
"""

from flask import Flask, jsonify
from flask_cors import CORS
from werkzeug.exceptions import RequestEntityTooLarge

from .ai import ai_bp
from .config import Config
from .extensions import db, migrate
from .routes.admin import admin_bp
from .routes.attractions import attractions_bp
from .routes.auth import auth_bp
from .routes.chat import chat_bp
from .routes.images import images_bp
from .routes.interactions import interactions_bp
from .routes.hotels import hotels_bp
from .routes.itineraries import itineraries_bp
from .routes.recommendations import recommendations_bp
from .routes.users import users_bp
from .routes.weather import weather_bp
from .seed import register_cli


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)
    CORS(app)  # dev-only: allow the Vite dev server to call the API.

    # Database + migrations.
    db.init_app(app)
    migrate.init_app(app, db)

    # Import models so their metadata is registered (needed for Alembic autogen).
    from . import models  # noqa: F401

    # Blueprints.
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(admin_bp, url_prefix="/api/admin")
    app.register_blueprint(ai_bp, url_prefix="/api/ai")
    app.register_blueprint(attractions_bp, url_prefix="/api")
    app.register_blueprint(chat_bp, url_prefix="/api")
    app.register_blueprint(images_bp, url_prefix="/api")
    app.register_blueprint(interactions_bp, url_prefix="/api")
    app.register_blueprint(hotels_bp, url_prefix="/api")
    app.register_blueprint(itineraries_bp, url_prefix="/api")
    app.register_blueprint(recommendations_bp, url_prefix="/api")
    app.register_blueprint(users_bp, url_prefix="/api/users")
    app.register_blueprint(weather_bp, url_prefix="/api")

    # CLI commands (flask seed-db).
    register_cli(app)

    # Oversized uploads abort during body parsing (MAX_CONTENT_LENGTH), before
    # any route runs — translate to the shared JSON error shape here.
    @app.errorhandler(RequestEntityTooLarge)
    def _too_large(_exc):
        limit_mb = app.config["MAX_CONTENT_LENGTH"] // (1024 * 1024)
        return jsonify({"error": f"File is too large (max {limit_mb} MB)."}), 413

    @app.get("/health")
    def health():
        return jsonify({"status": "ok", "service": "tourmateai-backend"})

    return app
