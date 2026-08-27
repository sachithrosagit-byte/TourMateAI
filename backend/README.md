# backend/ — Application Tier (Flask)

A single Flask application (modular monolith). **Ownership is split inside this folder** — read the
map carefully to avoid conflicts.

## Ownership map

| Path | Owner | Purpose |
|------|-------|---------|
| `app/__init__.py` | **Web dev** | App factory; creates app, registers blueprints (incl. `app.ai`) |
| `app/config.py` *(to be added)* | **Web dev** | Env-driven config |
| `app/models/` | **Web dev** | SQLAlchemy models for the shared schema |
| `app/routes/` | **Web dev** | Web/business endpoints (auth, users, attractions, feedback) |
| `app/services/` | **Web dev** | External integrations: Firebase, Google Maps, OpenWeather |
| `app/ai/` | **AI dev** | AI package — Blueprint mounted at `/api/ai/*` (see `app/ai/README.md`) |
| `tests/` | **Shared** | Unit/integration tests (each owner tests their area) |
| `run.py` *(to be added)* | **Web dev** | Entry point |

**Integration point:** the web dev's app factory imports and registers the AI blueprint. Until the
real AI modules exist, a mock blueprint (owned by AI dev) can return sample JSON so the frontend and
backend can be built in parallel. See `plan.md` Phase 0.5.

## Setup

```
python -m venv venv
venv\Scripts\Activate.ps1        # Windows PowerShell
pip install -r requirements.txt
python run.py                     # once run.py exists
```

## Testing

```
pytest                                   # all
pytest tests/test_recommender.py         # one file
pytest tests/test_recommender.py::test_x # one test
```

## Rules

- Config/secrets come from `.env` (see repo-root `.env.example`); never hardcode keys.
- AI dev and web dev communicate only through the JSON contracts in `../docs/api-contract.md` and
  the shared DB models. Don't reach across the `app/ai/` boundary in either direction.
