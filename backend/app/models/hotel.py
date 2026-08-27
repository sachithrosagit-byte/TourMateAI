"""Hotel model — for storing accommodation data."""

from datetime import datetime
from ..extensions import db


class Hotel(db.Model):
    __tablename__ = "Hotels"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    location = db.Column(db.String(100), index=True)  # e.g., 'Galle', 'Kandy'
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    image_url = db.Column(db.String(500))
    avg_rating = db.Column(db.Float, default=0)
    budget_tier = db.Column(db.String(50), index=True)  # 'budget', 'mid-range', 'luxury'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    itinerary_items = db.relationship(
        "ItineraryItem", back_populates="hotel", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Hotel {self.id} {self.name} ({self.budget_tier})>"

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "image_url": self.image_url,
            "avg_rating": self.avg_rating,
            "budget_tier": self.budget_tier,
        }
