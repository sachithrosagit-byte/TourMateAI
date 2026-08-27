# API Contract — AI Endpoints

**Source of truth** for how the frontend/backend talk to the AI package (`backend/app/ai/`).
Both developers code against this. If a shape must change, update this file and notify the other
developer. Version bumps go in the changelog at the bottom.

All AI endpoints are mounted under `/api/ai/` and exchange JSON (except image upload, which is
multipart). Auth: requests are expected to come from the authenticated backend context.

> **Status:** DRAFT v0.1 — mock responses first (Phase 0.5), real implementations in Phases 3–5.
> Shapes may be refined during Phase 0; freeze before parallel work begins in earnest.

---

## 1. `POST /api/ai/recommend`

Personalized, context-aware attraction recommendations.

> **Placeholder until this ships:** the Dashboard currently calls
> `GET /api/recommendations/mock` (auth required, web-side — see
> `backend/app/routes/recommendations.py`), which filters attractions by the
> user's stored interests. Its items carry the same `score` + `reason` fields
> plus full attraction data, so the frontend swap is confined to
> `frontend/src/services/recommendations.js`.

**Request**
```json
{
  "user_id": "abc123",
  "preferences": {
    "interests": ["cultural", "historical"],
    "budget": "medium",
    "duration_days": 3
  },
  "context": {
    "location": { "lat": 6.9271, "lng": 79.8612 },
    "weather": "clear",
    "time": "2026-07-02T09:00:00Z"
  }
}
```

**Response**
```json
{
  "recommendations": [
    {
      "attraction_id": 42,
      "name": "Temple of the Tooth",
      "score": 0.93,
      "reason": "Matches your interest in cultural & historical sites"
    }
  ]
}
```

---

## 2. `POST /api/ai/chat`

RAG chatbot turn. Answers are grounded in the knowledge base; `sources` are always returned.

**Request**
```json
{
  "session_id": "sess-001",
  "message": "Best time to visit Sigiriya?",
  "context": {
    "location": { "lat": 7.957, "lng": 80.760 },
    "weather": "clear"
  }
}
```

**Response**
```json
{
  "reply": "Early morning (7–9 AM) is best to avoid heat and crowds...",
  "sources": [ { "attraction_id": 7, "title": "Sigiriya", "snippet": "..." } ],
  "suggestions": ["Nearby: Pidurangala Rock", "Ask about entrance fees"]
}
```

If retrieval finds nothing relevant, `reply` should say so rather than hallucinate, and `sources`
will be `[]`.

---

## 3. `POST /api/ai/identify`

Landmark identification from an uploaded image. **multipart/form-data**, field name `image`.

**Response**
```json
{
  "landmark": "Sigiriya",
  "confidence": 0.87,
  "info": {
    "name": "Sigiriya Rock Fortress",
    "location": "Matale District",
    "history": "5th-century rock fortress and palace ruins..."
  },
  "nearby": [ { "attraction_id": 8, "name": "Dambulla Cave Temple" } ]
}
```

If confidence is below threshold: `{ "landmark": null, "confidence": <low>, "message": "Not recognized" }`.

---

## 4. `POST /api/ai/plan`

AI-driven itinerary planner that uses LangGraph agents to search flights, hotels, and generate a travel itinerary based on a user's prompt.

**Request**
```json
{
  "message": "Plan a 3 day budget trip to Colombo from New York",
  "thread_id": "optional-thread-id-for-conversation-memory"
}
```

**Response**
```json
{
  "thread_id": "user_abc123",
  "answer": "Here is your 3-day itinerary...",
  "itinerary": "Day 1: ...",
  "flight_results": "Flight options...",
  "hotel_results": "Hotel options...",
  "llm_calls": 4
}
```

---

## Conventions

- Errors: `{ "error": "message" }` with an appropriate HTTP status.
- Timestamps: ISO 8601 UTC. Coordinates: decimal degrees.
- Target latency: < 3s per call (proposal NFR).

## Changelog

- **v0.1** — initial draft (recommend / chat / identify).
