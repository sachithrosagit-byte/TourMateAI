"""ChatLog model — chatbot conversation history.

`response` is populated by the teammate's RAG chatbot feature.
"""

from datetime import datetime

from ..extensions import db

# Allowed values for ``quality_flag`` (besides NULL). The admin monitoring view
# offers exactly these when marking a bot reply.
QUALITY_FLAGS = ("unhelpful", "incorrect")


class ChatLog(db.Model):
    __tablename__ = "ChatLogs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    session_id = db.Column(
        db.Integer,
        db.ForeignKey("ChatSessions.id", ondelete="CASCADE"),
        nullable=True, # Will be set to False after migration creates default sessions
        index=True,
    )
    message = db.Column(db.Text, nullable=False)
    response = db.Column(db.Text)  # filled in by the chatbot
    # Admin chatbot-accuracy review. NULL = unreviewed; otherwise one of
    # QUALITY_FLAGS ("unhelpful" | "incorrect"). Set from the admin Chatbot
    # Monitoring view so the AI teammate can spot weak answers to retrain on.
    quality_flag = db.Column(db.String(20), index=True)
    # Attraction ids the reply suggested (list[int], may be empty/None) — kept so
    # the Chat page can re-render the inline attraction cards when the user's
    # conversation is reloaded from history, not just the text.
    suggested_attractions = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship("User", back_populates="chat_logs")
    session = db.relationship("ChatSession", back_populates="chat_logs")

    def __repr__(self):
        return f"<ChatLog {self.id} u{self.user_id}>"
