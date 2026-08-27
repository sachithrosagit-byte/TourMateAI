from datetime import datetime

from ..extensions import db


class ChatSession(db.Model):
    __tablename__ = "ChatSessions"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = db.Column(db.String(255), nullable=False, default="New Chat")
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="chat_sessions")
    chat_logs = db.relationship("ChatLog", back_populates="session", cascade="all, delete-orphan", order_by="ChatLog.created_at")

    def __repr__(self):
        return f"<ChatSession {self.id} '{self.title}'>"
