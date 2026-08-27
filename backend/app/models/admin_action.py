"""AdminAction model — an audit trail of admin-portal actions.

Right now its only producer is the "Request retraining" control in the admin
Retraining & Dataset panel: pressing it logs a ``retraining_request`` row rather
than kicking off a real training run. The AI teammate can later watch this table
(or its ``GET /api/admin/retraining/history`` endpoint) and wire the request up
to their actual pipeline. Kept generic (a single ``action_type`` string) so other
auditable admin actions can reuse the table without a schema change.
"""

from datetime import datetime

from ..extensions import db

# Known ``action_type`` values. Free-form column (no DB enum) so new action kinds
# don't need a migration, but these are the ones the app writes today.
RETRAINING_REQUEST = "retraining_request"


class AdminAction(db.Model):
    __tablename__ = "AdminActions"

    id = db.Column(db.Integer, primary_key=True)
    # Who performed it. Nullable + SET NULL so the audit row survives even if the
    # admin's user account is later removed (the history shouldn't disappear).
    admin_id = db.Column(
        db.Integer,
        db.ForeignKey("Users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    action_type = db.Column(db.String(50), nullable=False, index=True)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # No back_populates: User doesn't need to know about its audit rows, and this
    # keeps the shared User model untouched.
    admin = db.relationship("User")

    def __repr__(self):
        return f"<AdminAction {self.id} {self.action_type} by u{self.admin_id}>"
