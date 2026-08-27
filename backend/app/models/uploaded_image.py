"""UploadedImage model — images users upload for landmark recognition.

`recognition_result` (JSON) is populated by the teammate's image-recognition
feature (landmark, confidence, matched attraction, etc.).
"""

from datetime import datetime

from ..extensions import db


class UploadedImage(db.Model):
    __tablename__ = "UploadedImages"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    image_url = db.Column(db.String(500), nullable=False)
    recognition_result = db.Column(db.JSON)  # filled in by the vision model
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="uploaded_images")

    def __repr__(self):
        return f"<UploadedImage {self.id} u{self.user_id}>"
