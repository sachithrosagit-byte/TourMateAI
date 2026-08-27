# TourMateAI — Implementation Plan

Step-by-step build plan for **TourMateAI**, an AI-based travel companion for Sri Lanka.
This plan is organized by **phases** and **two parallel tracks** so both developers can work at the
same time without blocking each other. **No time estimates** are given by request — this is a
dependency-ordered plan, not a schedule.

## How to read this plan

- **Tracks:**
  - **AI Track** — owned by *me* (recommendation engine, RAG chatbot, image recognition, datasets).
  - **Web Track** — owned by *teammate* (React frontend + Flask backend skeleton + auth + external
    APIs + admin portal).
- **Shared phases** (0, 1, 6, 7, 8) require coordination; the middle phases (2–5) run in parallel.
- Each step lists: **goal → sub-steps → done-when**.
- Decisions already made are in `CLAUDE.md` ("Key Decisions"). Open decisions are flagged
  **[DECISION POINT]**.

## Tech Stack (locked)

| Layer | Technology |
|-------|-----------|
| Frontend | React (Vite) |
| Backend | Python Flask (single app, modular monolith) |
| Database | MySQL (SQLAlchemy models) |
| Auth | Firebase Authentication |
| Recommendation | scikit-learn (content-based filtering, cosine similarity) |
| Chatbot | **LLM + RAG**: Google Gemini API + ChromaDB + sentence-transformers |
| Image recognition | TensorFlow/Keras CNN — **[DECISION POINT]** scratch vs transfer learning |
| External APIs | Google Maps, OpenWeather |

---

## Phase 0 — Foundations & Contracts (SHARED, do together first)

**Goal:** Agree on everything both sides depend on, so parallel work never blocks.

0.1 **Repo & structure**
- Initialize git repo. Create the folder layout from `CLAUDE.md` (`frontend/`, `backend/`,
  `ai_lab/`). The data tier lives inside `backend/` (SQLAlchemy models + Alembic migrations).
- Add `.gitignore` (node_modules, venv, `.env`, `ai_lab/models/*`, large datasets) and
  `.env.example`.

0.2 **Accounts, keys & tooling**
- Create: Firebase project, Google Cloud project (Maps + Gemini API enabled), OpenWeather account.
- Put keys in `.env` locally; document key names in `.env.example`.
- Confirm free-tier limits for Gemini, Maps, OpenWeather and note them.

0.3 **Database schema (design together, this is the shared backbone)**
- Tables (from proposal): **Users, Attractions, Interactions, Images, Feedback** (+ `ChatSessions`
  for chat history).
- `Attractions` must carry the metadata the recommender needs: `type/category`, `location (lat/lng)`,
  `popularity`, `tags`, `description`. This table feeds both the recommender and the RAG KB.
- Implement as SQLAlchemy models in `backend/app/models/`, version with Flask-Migrate
  (`backend/migrations/`), and seed via `flask seed-db` (`backend/app/seed.py`).

0.4 **API contracts (freeze these — see `CLAUDE.md`)**
- `POST /api/ai/recommend`, `POST /api/ai/chat`, `POST /api/ai/identify` — request/response JSON.
- Web endpoints the frontend needs (auth, profile, attractions, feedback) — teammate drafts.
- Write these into a short `docs/api-contract.md` both sides code against.

0.5 **Flask app factory skeleton (teammate, but AI needs the hook)**
- Minimal `backend/app/__init__.py` app factory that registers a **blueprint stub** at `/api/ai/*`.
- I provide a placeholder `app/ai/blueprint.py` returning mock responses so the frontend can be
  built before the real models exist.

**Done when:** repo scaffolds run, schema is agreed, contracts are frozen, and a mock `/api/ai/*`
returns sample JSON.

---

## Phase 1 — Data Foundation (AI Track leads; needed before real AI works)

**Goal:** Assemble and clean the data every AI module depends on. Start this early — data collection
is the long pole.

1.1 **Tourism / attractions dataset**
- Collect Sri Lanka attractions data (public tourism datasets, SLTDA, curated CSV).
- Clean & normalize into the `Attractions` schema fields (category, tags, location, popularity,
  description). Store processed data in `ai_lab/datasets/` and seed into MySQL.

1.2 **RAG knowledge base corpus**
- Gather text about attractions (descriptions, history, travel tips, FAQ, routes, costs).
- Chunk into passages with metadata (attraction id, source) for retrieval.

1.3 **Landmark image dataset**
- Collect labeled images of Sri Lankan landmarks (+ a few global) — target a workable number of
  classes with enough images/class. Split train/val/test.
- Note in a `ai_lab/datasets/README.md`: sources, licenses, class list, counts.

**Done when:** processed attractions data seeds the DB; KB corpus is chunked; image dataset is
split and documented.

---

## Phase 2 — Web Track (teammate, parallel with Phases 2–5 AI work)

**Goal:** Full web application working end-to-end against the **mock** `/api/ai/*` until real
modules land.

2.1 **Backend core**
- Flask app factory, config, SQLAlchemy models for the Phase 0 schema, DB connection.
- Error handling, CORS, logging, health check.

2.2 **Auth & users**
- Firebase Authentication (register/login), token verification middleware.
- User profile + preferences endpoints (interests, budget, trip duration) — these feed
  `/api/ai/recommend`.

2.3 **Core business endpoints**
- Attractions listing/detail, feedback submission, interaction logging (views/selects — the
  recommender uses these later).

2.4 **External API services**
- `services/maps.py` (Google Maps: geocoding, routing, nearby), `services/weather.py` (OpenWeather).
- Endpoint(s) that assemble **context** (location + weather + time) to pass into AI calls.

2.5 **React frontend**
- Scaffold Vite + React, routing, auth pages, API client.
- Feature pages: dashboard, **recommendations**, **chatbot**, **image upload/identify**, maps +
  weather, profile.
- Admin portal: manage attractions/feedback, view analytics, trigger dataset/model refresh.

2.6 **Wire frontend ↔ backend** against mock AI, then later against real AI (Phase 6).

**Done when:** a user can register, log in, browse attractions, and use recommendation/chat/image
UIs driven by mock AI responses.

---

## Phase 3 — AI Module: Content-Based Recommendation Engine (AI Track)

**Goal:** Personalized attraction recommendations, context-aware, ≥80% accuracy target.

3.1 **Feature engineering**
- Build attraction feature vectors from metadata (category, tags, popularity, location) using
  TF-IDF / one-hot + scaling. Build a user-preference vector from profile + interaction history.

3.2 **Similarity model**
- Content-based filtering with cosine similarity (scikit-learn) to rank attractions for a user.

3.3 **Context-aware re-ranking**
- Adjust scores using weather (e.g. indoor vs outdoor), time, and proximity to the user's location.

3.4 **Feedback loop**
- Incorporate `Interactions`/`Feedback` so repeated cultural-site views push similar sites up
  (the proposal's example).

3.5 **Expose + evaluate**
- Implement the real `POST /api/ai/recommend` in `app/ai/recommender/`.
- Evaluate accuracy (precision@k / hit-rate against a labeled holdout) targeting **≥80%**; script in
  `ai_lab/training/evaluate.py`.

**Done when:** endpoint returns ranked, context-adjusted recommendations with reasons and meets the
accuracy target on the eval set.

---

## Phase 4 — AI Module: RAG Chatbot (AI Track)

**Goal:** Conversational travel Q&A grounded in the KB, multilingual, using Gemini.

4.1 **Embeddings + vector store**
- Embed the Phase 1 KB chunks with **sentence-transformers**; index in **ChromaDB**.
- `ai_lab/training/build_kb.py` builds/refreshes the index; app loads it read-only at startup.

4.2 **Retrieval**
- Given a user message, embed it, retrieve top-k relevant chunks (with metadata for `sources`).

4.3 **Generation (Gemini)**
- Prompt Gemini with retrieved context + conversation history. **Grounding rule:** answer only from
  context; if retrieval is empty/weak, say so — no free hallucination. Always return `sources`.
- Inject **context** (location/weather) so answers about routes/costs/weather are situational.

4.4 **Conversation & multilingual**
- Session memory via `ChatSessions`. Support multilingual Q&A (Gemini handles translation; optionally
  Google Translate for edge cases).

4.5 **Expose + safeguards**
- Implement real `POST /api/ai/chat` in `app/ai/chatbot/`.
- Handle Gemini rate limits/quota gracefully; cache frequent Q&A; keep responses < 3s where possible.

**Done when:** chatbot answers tourism questions grounded in KB with cited sources, remembers session
context, and degrades gracefully on quota limits.

---

## Phase 5 — AI Module: Image / Landmark Recognition (AI Track)

**Goal:** Identify a landmark from a photo and return info + related suggestions.

5.1 **Preprocessing pipeline**
- Resizing, normalization, augmentation for the Phase 1 image dataset.

5.2 **[DECISION POINT] Model approach — benchmark both, then pick**
- **Option A — CNN from scratch:** custom Keras CNN. More educational, needs more data, typically
  lower accuracy.
- **Option B — Transfer learning:** take a pretrained backbone (ResNet / MobileNet / EfficientNet)
  and **fine-tune** it on our landmarks. *Note:* this still requires training (fine-tuning), just
  much less data/time, and usually much higher accuracy. Fully acceptable academically.
- Train both (`ai_lab/training/train_cnn.py`), compare accuracy/latency/size on the test split,
  **document the comparison**, and choose the winner. Record the decision here and in `CLAUDE.md`.

5.3 **Inference + enrichment**
- Load the chosen model in `app/ai/vision/`. On identification, join to the `Attractions`/KB data to
  return name, location, history, and nearby attractions + suggested itinerary.

5.4 **Expose**
- Implement real `POST /api/ai/identify` (multipart upload). Add a confidence threshold / "not
  recognized" fallback.

**Done when:** uploading a landmark photo returns the correct place (above threshold) with enriched
info, and the model choice is justified with metrics.

---

## Phase 6 — Integration (SHARED)

**Goal:** Replace mocks with real AI and run the whole system together.

6.1 Register real `app/ai/` blueprint in the teammate's Flask app; remove mock responses.
6.2 Point the React frontend at the real endpoints; verify each contract end-to-end.
6.3 Wire context flow: frontend/geolocation → Maps/Weather services → AI calls.
6.4 Fix contract mismatches (adjust and re-version `docs/api-contract.md` if needed).

**Done when:** recommendations, chat, and image ID all work through the real UI against real models.

---

## Phase 7 — Testing & Evaluation (SHARED)

**Goal:** Verify functionality and hit the proposal's success metrics.

7.1 **Unit tests** — recommender scoring, retrieval, model inference, services (mock external APIs).
7.2 **Integration tests** — each `/api/ai/*` and web endpoint end-to-end.
7.3 **Metrics** — recommendation accuracy (**≥80%**), AI response time (**<3s**), image accuracy,
    chatbot answer quality.
7.4 **UAT** — trial with sample users/guides; collect feedback; iterate (user-centered loop from the
    proposal).

**Done when:** tests pass and metrics are recorded in the evaluation report.

---

## Phase 8 — Documentation & Deployment (SHARED)

**Goal:** Ship the deliverables listed in the proposal.

8.1 **Technical documentation** — architecture, API endpoints, DB schema, setup guide.
8.2 **User manual** + **Admin guide**.
8.3 **Source code package** — clean, commented, organized (both tracks).
8.4 **Testing & Evaluation report** — methodology + results vs targets.
8.5 **Deployment** — deploy frontend + backend + DB; document the deployment steps.

**Done when:** all seven proposal deliverables exist and the app is deployed/reproducible.

---

## Dependency Summary

```
Phase 0 (shared) ─┬─► Phase 1 (data, AI) ─┬─► Phase 3 Recommender ─┐
                  │                        ├─► Phase 4 RAG Chatbot ─┤
                  │                        └─► Phase 5 Image Recog ─┼─► Phase 6 ─► Phase 7 ─► Phase 8
                  └─► Phase 2 (web, teammate) ──────────────────────┘
```

- Web Track (Phase 2) runs against **mock AI** the whole time, so it never waits on AI.
- AI Track (Phases 3–5) can be built in any order once Phase 1 data exists; recommender first is
  recommended (simplest, unblocks the core UX).

## Open Decisions to Finalize Later

1. **[DECISION POINT] Image model:** scratch CNN vs transfer-learning backbone — decide after the
   Phase 5.2 benchmark.
2. **Multilingual depth:** rely on Gemini alone vs. add Google Translate for specific flows.
3. **Deployment target:** where frontend/backend/DB are hosted (revisit at Phase 8).

## Deliverables → Phase Map (from the proposal)

| Proposal deliverable | Delivered in |
|----------------------|--------------|
| Functional web app prototype (React) | Phase 2, 6 |
| AI backend (3 modules) | Phases 3, 4, 5 |
| MySQL database | Phase 0, 1 |
| API integrations + context-aware services | Phase 2.4, 6.3 |
| Project documentation | Phase 8 |
| Source code & deployment package | Phase 8 |
| Testing & evaluation report | Phase 7, 8 |
