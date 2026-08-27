"""Shared pytest fixtures.

Runs the real app factory against an in-memory SQLite DB (no MySQL needed) and
stubs Firebase token verification so authenticated routes can be tested without
real credentials. A bearer token of ``valid-<uid>`` is accepted and decodes to
that uid; anything else is rejected like a real invalid token.
"""

import pytest

from app import create_app
import app.routes.auth as auth_module
from app.config import Config
from app.extensions import db
from app.models import Attraction


class _TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"


def _fake_verify_token(id_token):
    """Decode ``valid-<uid>`` tokens; reject everything else."""
    if not id_token.startswith("valid-"):
        from firebase_admin import auth as firebase_auth

        raise firebase_auth.InvalidIdTokenError("invalid test token")
    uid = id_token[len("valid-") :]
    return {"uid": uid, "email": f"{uid}@example.com", "name": uid}


@pytest.fixture
def app(monkeypatch):
    monkeypatch.setattr(auth_module, "verify_token", _fake_verify_token)
    app = create_app(_TestConfig)
    with app.app_context():
        db.create_all()
        db.session.add_all(
            [
                Attraction(
                    name="Sigiriya Rock Fortress", category="Heritage",
                    description="Ancient rock fortress with frescoes.",
                    latitude=7.957, longitude=80.76,
                ),
                Attraction(
                    name="Galle Fort", category="Historical",
                    description="Fortified colonial old town on the coast.",
                    latitude=6.02, longitude=80.21,
                ),
                Attraction(
                    name="Mirissa Beach", category="Beach",
                    description="Southern beach known for whale watching.",
                    latitude=5.94, longitude=80.45,
                ),
            ]
        )
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def auth_headers():
    """Authorization header for test user ``user1``."""
    return {"Authorization": "Bearer valid-user1"}
