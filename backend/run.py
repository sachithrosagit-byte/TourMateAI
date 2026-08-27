"""Development entrypoint for the TourMateAI Flask backend.

    cd backend
    python run.py

Serves the AI endpoints (mock in Phase 0.5) at http://localhost:5000/api/ai/*.
Production/deployment wiring is decided later (Phase 8).
"""

import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_ENV", "development") != "production"
    app.run(host="0.0.0.0", port=port, debug=debug)
