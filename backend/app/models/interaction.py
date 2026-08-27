"""Interaction model — user↔attraction signals for the recommendation engine.

Kept deliberately generic (a single typed event table) and well-indexed on the
columns the recommender will query most: user_id, attraction_id.
"""

import enum
from datetime import datetime

from ..extensions import db


class InteractionType(enum.Enum):
    view = "view"
    like = "like"
    visit = "visit"


class Interaction(db.Model):
    __tablename__ = "Interactions"

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
    interaction_type = db.Column(db.Enum(InteractionType), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="interactions")
    attraction = db.relationship("Attraction", back_populates="interactions")

    # Composite index for the recommender's per-user / per-attraction lookups.
    __table_args__ = (
        db.Index("ix_interactions_user_attraction", "user_id", "attraction_id"),
    )

    def __repr__(self):
        return (
            f"<Interaction {self.id} u{self.user_id} a{self.attraction_id} "
            f"{self.interaction_type.value if self.interaction_type else None}>"
        )
