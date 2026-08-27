"""Shared Flask extension singletons.

Kept in their own module (rather than app/__init__.py) so models and the app
factory can both import them without circular-import problems.
"""

from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
migrate = Migrate()
