"""Attraction model — the shared join point.

The recommender ranks these, the RAG knowledge base is built from their
descriptions, and image recognition enriches results from them.
"""

from datetime import datetime

from ..extensions import db


class Attraction(db.Model):
    __tablename__ = "Attractions"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(80), index=True)  # frequently filtered/queried
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    avg_rating = db.Column(db.Float, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    interactions = db.relationship(
        "Interaction", back_populates="attraction", cascade="all, delete-orphan"
    )
    itinerary_items = db.relationship(
        "ItineraryItem", back_populates="attraction", cascade="all, delete-orphan"
    )
    feedback = db.relationship(
        "Feedback", back_populates="attraction", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Attraction {self.id} {self.name}>"
