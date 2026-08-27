"""SQLAlchemy models for the shared TourMateAI schema.

Importing this package registers every model's metadata with SQLAlchemy so that
Flask-Migrate/Alembic can autogenerate migrations. The app factory imports it.
"""

from ..extensions import db
from .admin_action import AdminAction
from .attraction import Attraction
from .chat_session import ChatSession
from .chat_log import ChatLog
from .feedback import Feedback
from .hotel import Hotel
from .interaction import Interaction, InteractionType
from .itinerary import Itinerary, ItineraryItem
from .uploaded_image import UploadedImage
from .user import User

__all__ = [
    "db",
    "User",
    "AdminAction",
    "Attraction",
    "Interaction",
    "InteractionType",
    "Itinerary",
    "ItineraryItem",
    "Feedback",
    "ChatSession",
    "ChatLog",
    "UploadedImage",
    "Hotel",
]
