# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**TourMateAI** — *An Intelligent AI-Based Travel Companion* — is an AI-powered tourism assistant
focused on Sri Lanka. It delivers personalized, context-aware (location + weather + time) travel
help through a web application backed by three AI capabilities:

1. **Content-Based Recommendation Engine** — personalized attraction suggestions.
2. **RAG Chatbot** — conversational travel Q&A grounded in a Sri Lanka tourism knowledge base.
3. **Image / Landmark Recognition** — identify a landmark from an uploaded photo and return info + related suggestions.

This is a university final project (CIS6035, Cardiff Metropolitan / ICBT). Academic prototype
scope, MVP quality, free-tier tooling.

> **Status:** Phase 0 scaffolding is in place — the full directory tree, per-area `README.md`s,
> empty package `__init__.py` stubs, `backend/requirements.txt`, `.env.example`, and
> `docs/api-contract.md` all exist. What does **not** exist yet: the Flask app factory
> (`backend/app/__init__.py` is empty), `backend/run.py`, and `backend/app/ai/blueprint.py`. So the
> layout below is real, but the run/test commands only work once those files are written. Update
> this note as modules land.

## Key Decisions (these override the original proposal)

The PDF proposal in `docs/Project_Proposal.pdf` is the baseline, but the following decisions
**supersede** it:

| Area | Proposal said | We use instead |
|------|---------------|----------------|
| Frontend | HTML/CSS/JS (in Deliverables) | **React** (Vite) — confirmed by architecture section |
| Chatbot NLP | BERT / TF-IDF + Logistic Regression | **LLM + RAG**: Google **Gemini API** + **ChromaDB** + **sentence-transformers** |
| Vector store | (n/a) | **ChromaDB** with local **sentence-transformers** embeddings (no API cost) |
| Image model | Custom CNN from scratch | **Undecided** — benchmark *CNN-from-scratch* vs *transfer learning* (ResNet/MobileNet/EfficientNet), pick the winner |

Unchanged from the proposal: Python **Flask** backend, **MySQL** database, **Firebase**
Authentication, **Google Maps** API, **OpenWeather** API, three-tier architecture.

## Team Split & Ownership

Two developers work **in parallel**:

- **AI Developer (repo owner, "me"):** all AI features — recommendation engine, RAG chatbot,
  image recognition, plus the datasets/training that back them.
- **Web Developer (teammate):** React frontend **and** the Flask backend skeleton (app factory,
  routing, DB models, Firebase auth, Google Maps / OpenWeather integration, admin portal).

**Boundary rule:** The AI code lives as a self-contained package (`backend/app/ai/`) that the
teammate's Flask app mounts as a Blueprint. The two sides meet **only** at agreed HTTP/JSON
contracts and the shared DB schema — so both can build without blocking each other. Do not let AI
code reach into web routes or vice versa except through those contracts.

## Architecture

Three-tier, single deployable **modular monolith** (no microservices):

```
React (Vite) SPA  ──HTTP/JSON──►  Flask backend  ──►  MySQL
                                     │
                                     ├── web/business routes, Firebase auth, Maps/Weather   (teammate)
                                     └── app/ai/  Blueprint  →  /api/ai/*                    (me)
                                            ├── recommender/   content-based filtering (scikit-learn)
                                            ├── chatbot/       RAG: ChromaDB + sentence-transformers + Gemini
                                            └── vision/        CNN landmark classifier (TensorFlow/Keras)
```

The AI package is imported and registered by the teammate's app factory. It exposes plain HTTP
endpoints so it can also be exercised standalone during development.

### Intended repository layout

```
TourMateAI/
├── docs/                     # proposal + generated technical docs
├── frontend/                 # React + Vite SPA                              (teammate)
├── backend/
│   ├── app/
│   │   ├── __init__.py       # Flask app factory; registers blueprints
│   │   ├── config.py         # env-driven config (builds MySQL URI from .env)
│   │   ├── extensions.py     # db + migrate singletons (avoid circular imports)
│   │   ├── models/           # SQLAlchemy models (shared schema — the data tier)
│   │   ├── seed.py           # `flask seed-db` — sample Sri Lankan attractions
│   │   ├── routes/           # web/business endpoints                        (teammate)
│   │   ├── services/         # Google Maps, OpenWeather, Firebase            (teammate)
│   │   └── ai/               # ← AI package                                  (me)
│   │       ├── blueprint.py  # /api/ai/recommend, /chat, /identify
│   │       ├── recommender/
│   │       ├── chatbot/
│   │       ├── vision/
│   │       └── shared/       # config, schemas, context helpers
│   ├── migrations/           # Alembic (Flask-Migrate) schema history
│   ├── tests/
│   ├── requirements.txt
│   └── run.py
├── ai_lab/                   # ← my experimentation (NOT shipped to prod)    (me)
│   ├── datasets/             # raw + processed tourism data & landmark images
│   ├── notebooks/            # EDA, prototyping
│   ├── training/             # training scripts (CNN, KB build, eval)
│   └── models/               # saved model artifacts loaded by app/ai/
├── CLAUDE.md
└── plan.md
```

## AI ↔ Backend Contracts (source of truth for parallel work)

These JSON contracts are what the teammate codes against. Keep them stable; version if they change.
**`docs/api-contract.md` is the fuller source of truth** (full request/response examples + changelog,
currently DRAFT v0.1) — the summary below must stay in sync with it.

- `POST /api/ai/recommend` → `{ user_id, preferences{interests[],budget,duration_days}, context{location,weather,time} }`
  ⇒ `{ recommendations: [{attraction_id, name, score, reason}] }`
- `POST /api/ai/chat` → `{ session_id, message, context{location,weather} }`
  ⇒ `{ reply, sources: [...], suggestions: [...] }`
- `POST /api/ai/identify` (multipart/form-data, field name `image`) → `{ landmark, confidence, info{name,location,history}, nearby: [...] }`; below threshold ⇒ `{ landmark: null, confidence, message }`

## Commands

> Windows host (PowerShell primary). Commands become valid after Phase 0 scaffolding.

**Frontend (`frontend/`)**
```
npm install
npm run dev            # Vite dev server
npm run build
npm run lint
```

**Backend (`backend/`)**
```
python -m venv venv
venv\Scripts\Activate.ps1
pip install -r requirements.txt
python run.py                              # or: flask run
pytest                                     # all tests
pytest tests/test_recommender.py           # one file
pytest tests/test_recommender.py::test_cosine_match   # one test
```

**AI training / data (`ai_lab/`)**
```
python ai_lab/training/build_kb.py         # build/refresh ChromaDB knowledge base for RAG
python ai_lab/training/train_cnn.py        # train / fine-tune landmark model → ai_lab/models/
python ai_lab/training/evaluate.py         # recommendation accuracy, model metrics
```

## Conventions & Constraints

- **Secrets:** API keys (Gemini, Google Maps, OpenWeather, Firebase) via `.env` only; never commit.
  `.env.example` is the authoritative key list — key names include `GEMINI_API_KEY`,
  `GOOGLE_MAPS_API_KEY`, `OPENWEATHER_API_KEY`, `FIREBASE_CREDENTIALS` (path to service-account JSON),
  `DB_*` (MySQL), `CHROMA_DB_PATH`, and `EMBEDDING_MODEL` (default `all-MiniLM-L6-v2`). Frontend uses
  its own `VITE_*` vars.
- **Dependencies:** `backend/requirements.txt` is intentionally **unpinned** for now — pin versions
  (`pip freeze`) once the environment is first set up in Phase 0, then commit the pinned file.
- **RAG grounding:** the chatbot must answer from retrieved KB context; if retrieval is empty, say
  so rather than let Gemini free-hallucinate. Always return `sources`.
- **Gemini free tier:** mind rate limits — cache where sensible, keep prompts lean, and fail
  gracefully when quota is hit. Model IDs and usage: consult the current Gemini docs, not memory.
- **Model artifacts:** trained models live in `ai_lab/models/` and are loaded by `app/ai/`; do not
  retrain on request start. Large artifacts/datasets should be git-ignored or tracked via LFS.
- **Non-functional targets (from proposal):** AI responses < 3s; recommendation accuracy ≥ 80%.
- **Context-aware everything:** recommendations and chat should factor in location + weather + time
  supplied by the backend (via Maps/Weather services).
