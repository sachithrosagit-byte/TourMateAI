"""Admin portal — every endpoint here requires ``is_admin`` (``@require_admin``).

Backs the React admin dashboard. Registered by the app factory at
``/api/admin/*``. The portal is split into focused route modules, all sharing
one blueprint:

  - ``attractions`` — catalogue CRUD, bulk category/delete, CSV import/export,
                      photo upload/serve
  - ``users``       — user list (search / date + activity filters) + per-user
                      interaction & feedback history
  - ``feedback``    — moderation: list all reviews, hide/unhide, delete
  - ``chatlogs``    — chatbot accuracy monitoring: transcripts, volume over time,
                      quality flagging
  - ``retraining``  — dataset stats + a "request retraining" audit action
  - ``analytics``   — headline totals plus engagement / feedback / chat / image
                      breakdowns

Attractions are the join point the recommender ranks and the RAG KB is built
from, so admin edits here flow straight into the AI features. ``category`` should
stay within the known set so user interests keep joining onto it.
"""

from flask import Blueprint

admin_bp = Blueprint("admin", __name__)

# Import the route modules for their side effect of attaching handlers to
# ``admin_bp``. ``admin_bp`` is already bound above, so ``from . import admin_bp``
# inside each module resolves without a cycle. Order is irrelevant.
from . import (  # noqa: E402,F401
    analytics,
    attractions,
    chatlogs,
    feedback,
    retraining,
    users,
)

__all__ = ["admin_bp"]
