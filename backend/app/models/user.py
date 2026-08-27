"""User model — app users and their travel preferences."""

from datetime import datetime

from ..extensions import db


class User(db.Model):
    __tablename__ = "Users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    firebase_uid = db.Column(db.String(128), unique=True, index=True)
    # Admin flag — gates the /api/admin/* endpoints and the React admin portal.
    # Flipped manually (flask set-admin <email>); there is no self-serve path.
    is_admin = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text("0")
    )
    chat_sessions = db.relationship(
        "ChatSession", back_populates="user", cascade="all, delete-orphan", order_by="ChatSession.created_at.desc()"
    )
    # Travel preferences — feeds the recommendation engine. Small, stable JSON:
    #   {
    #     "interests": ["Beach", "Wildlife"],  # subset of Attraction.category values
    #     "budget": "medium",                  # "low" | "medium" | "high"
    #     "pace": "moderate"                   # "relaxed" | "moderate" | "packed"
    #   }
    # Written via PUT /api/users/me (validated there); any key may be absent while
    # the profile is incomplete. See routes/users.py for the authoritative shape.
    preferences = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interactions = db.relationship(
        "Interaction", back_populates="user", cascade="all, delete-orphan"
    )
    itineraries = db.relationship(
        "Itinerary", back_populates="user", cascade="all, delete-orphan"
    )
    feedback = db.relationship(
        "Feedback", back_populates="user", cascade="all, delete-orphan"
    )
    chat_logs = db.relationship(
        "ChatLog", back_populates="user", cascade="all, delete-orphan"
    )
    uploaded_images = db.relationship(
        "UploadedImage", back_populates="user", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.id} {self.email}>"
