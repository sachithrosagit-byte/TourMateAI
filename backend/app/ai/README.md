# app/ai/ — AI Package (AI developer)

**Owner:** AI developer. This is the entire AI surface of TourMateAI, packaged so it plugs into the
Flask app as a single Blueprint mounted at `/api/ai/*`.

## Subpackages

| Package | Module | Responsibility |
|---------|--------|----------------|
| `recommender/` | Content-Based Recommendation Engine | Rank attractions for a user (scikit-learn, cosine similarity), context-aware re-ranking |
| `chatbot/` | RAG Chatbot | Retrieve from ChromaDB (sentence-transformers) + generate with Gemini; grounded answers with sources |
| `vision/` | Image Recognition | Identify a landmark from a photo (TensorFlow/Keras CNN), enrich with attraction info |
| `shared/` | Shared helpers | Config, request/response schemas, context (location/weather) utilities |
| `blueprint.py` *(to be added)* | Flask Blueprint | Exposes `/api/ai/recommend`, `/api/ai/chat`, `/api/ai/identify` |

## Contract with the backend

The web dev's app factory registers this blueprint. Endpoints and JSON shapes are frozen in
[`../../../docs/api-contract.md`](../../../docs/api-contract.md) — **treat that file as the source of
truth**. If a contract must change, update that doc and tell the web dev first.

## Where models & data live

- Trained artifacts (CNN weights, vectorizers, ChromaDB index) are produced in `ai_lab/` and loaded
  from here **at startup** — never train on request. See `../../../ai_lab/README.md`.
- Do not commit large model/data files (they're git-ignored); document how to rebuild them.

## Boundaries

- ✅ Owns everything under `app/ai/`.
- ❌ Do not edit `app/models/`, `app/routes/`, or `app/services/` — coordinate with the web dev
  instead.
