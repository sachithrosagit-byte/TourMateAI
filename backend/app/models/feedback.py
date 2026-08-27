"""Feedback model — user ratings/comments on attractions."""

from datetime import datetime

from ..extensions import db


class Feedback(db.Model):
    __tablename__ = "Feedback"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attraction_id = db.Column(
        db.Integer,
        db.ForeignKey("Attractions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    rating = db.Column(db.Integer, nullable=False)  # 1–5
    comment = db.Column(db.Text)
    # Moderation flag set from the admin feedback-moderation view. Hidden reviews
    # are kept (not deleted) for audit; the admin UI toggles this. Wiring it into
    # the public attraction reviews/average is a deliberate follow-up — the admin
    # pass doesn't change traveler-facing behaviour.
    is_hidden = db.Column(
        db.Boolean, nullable=False, default=False, server_default=db.text("0")
    )
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="feedback")
    attraction = db.relationship("Attraction", back_populates="feedback")

    def __repr__(self):
        return f"<Feedback {self.id} a{self.attraction_id} {self.rating}★>"
