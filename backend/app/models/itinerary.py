"""Itinerary models — a user's trip plan and its ordered day-by-day items."""

from datetime import datetime

from ..extensions import db


class Itinerary(db.Model):
    __tablename__ = "Itineraries"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    start_location = db.Column(db.String(200))
    end_location = db.Column(db.String(200))
    stops = db.Column(db.Text)
    start_date = db.Column(db.Date)
    end_date = db.Column(db.Date)
    trip_type = db.Column(db.String(50), default="Solo")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    is_ai_generated = db.Column(db.Boolean, default=False)

    user = db.relationship("User", back_populates="itineraries")
    items = db.relationship(
        "ItineraryItem",
        back_populates="itinerary",
        cascade="all, delete-orphan",
        order_by="ItineraryItem.day_number, ItineraryItem.order_index",
    )

    def __repr__(self):
        return f"<Itinerary {self.id} {self.title!r}>"


class ItineraryItem(db.Model):
    __tablename__ = "ItineraryItems"

    id = db.Column(db.Integer, primary_key=True)
    itinerary_id = db.Column(
        db.Integer,
        db.ForeignKey("Itineraries.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attraction_id = db.Column(
        db.Integer,
        db.ForeignKey("Attractions.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    hotel_id = db.Column(
        db.Integer,
        db.ForeignKey("Hotels.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    day_number = db.Column(db.Integer)
    order_index = db.Column(db.Integer)
    notes = db.Column(db.Text)

    itinerary = db.relationship("Itinerary", back_populates="items")
    attraction = db.relationship("Attraction", back_populates="itinerary_items")
    hotel = db.relationship("Hotel", back_populates="itinerary_items")

    def __repr__(self):
        return f"<ItineraryItem {self.id} it{self.itinerary_id} a{self.attraction_id}>"
