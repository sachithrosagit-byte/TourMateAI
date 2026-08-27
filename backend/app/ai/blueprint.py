"""AI package HTTP surface — the only thing the web/frontend side talks to.

Phase 0.5 status: these are **mock** implementations. They return sample data
shaped exactly like `docs/api-contract.md` so the frontend can be built before
the real models exist. Responses are *lightly dynamic* — they echo request
fields back (session_id, interests, filename, ...) so the caller can confirm
round-trip wiring, but no real recommendation / retrieval / inference happens.

Real implementations land in:
  - recommender/  → Phase 3   (POST /recommend)
  - chatbot/      → Phase 4   (POST /chat)
  - vision/       → Phase 5   (POST /identify)

Contract source of truth: docs/api-contract.md (keep in sync).
"""

from flask import Blueprint, jsonify, request

# Registered by the app factory at url_prefix="/api/ai", so routes below are
# the paths *after* that prefix (e.g. "/recommend" -> "/api/ai/recommend").
ai_bp = Blueprint("ai", __name__)

# Confidence below this is treated as "not recognized" by /identify.
IDENTIFY_CONFIDENCE_THRESHOLD = 0.5


@ai_bp.get("/health")
def health():
    """Liveness probe for the AI blueprint itself (mock or real)."""
    return jsonify({"status": "ok", "module": "ai", "mode": "mock"})


@ai_bp.post("/recommend")
def recommend():
    """Mock personalized recommendations — see api-contract.md §1.

    Lightly dynamic: reflects the caller's interests into each `reason` so the
    frontend can see its preferences round-trip.
    """
    body = request.get_json(silent=True) or {}
    preferences = body.get("preferences") or {}
    interests = preferences.get("interests") or []
    interest_phrase = " & ".join(interests) if interests else "your profile"

    recommendations = [
        {
            "attraction_id": 42,
            "name": "Temple of the Tooth",
            "score": 0.93,
            "reason": f"Matches your interest in {interest_phrase}",
        },
        {
            "attraction_id": 7,
            "name": "Sigiriya Rock Fortress",
            "score": 0.88,
            "reason": f"Popular pick aligned with {interest_phrase}",
        },
        {
            "attraction_id": 15,
            "name": "Galle Fort",
            "score": 0.81,
            "reason": "Coastal historical site, good in clear weather",
        },
    ]
    return jsonify({"recommendations": recommendations})


@ai_bp.post("/chat")
def chat():
    """Mock RAG chatbot turn — see api-contract.md §2.

    Lightly dynamic: echoes the user's message and session_id so the frontend
    can verify session wiring. Always returns `sources` per the grounding rule.
    """
    body = request.get_json(silent=True) or {}
    session_id = body.get("session_id", "unknown-session")
    message = (body.get("message") or "").strip()

    if not message:
        return jsonify({"error": "message is required"}), 400

    reply = (
        f"(mock reply for session {session_id}) You asked: \"{message}\". "
        "Early morning is generally the best time to visit hilltop and rock "
        "sites in Sri Lanka to avoid heat and crowds."
    )
    return jsonify(
        {
            "reply": reply,
            "sources": [
                {
                    "attraction_id": 7,
                    "title": "Sigiriya",
                    "snippet": "Best visited early morning...",
                }
            ],
            "suggestions": [
                "Nearby: Pidurangala Rock",
                "Ask about entrance fees",
            ],
        }
    )


@ai_bp.post("/identify")
def identify():
    """Mock landmark identification — see api-contract.md §3.

    Expects multipart/form-data with an `image` field. Lightly dynamic: echoes
    the uploaded filename. Missing file -> 400. Includes the below-threshold
    "not recognized" branch (toggle with ?confidence= for frontend testing).
    """
    image = request.files.get("image")
    if image is None:
        return jsonify({"error": "image file is required (field name 'image')"}), 400

    # Let the frontend exercise the low-confidence branch on demand.
    confidence = request.args.get("confidence", default=0.87, type=float)

    if confidence < IDENTIFY_CONFIDENCE_THRESHOLD:
        return jsonify(
            {
                "landmark": None,
                "confidence": confidence,
                "message": "Not recognized",
            }
        )

    return jsonify(
        {
            "landmark": "Sigiriya",
            "confidence": confidence,
            "info": {
                "name": "Sigiriya Rock Fortress",
                "location": "Matale District",
                "history": "5th-century rock fortress and palace ruins.",
            },
            "nearby": [
                {"attraction_id": 8, "name": "Dambulla Cave Temple"},
            ],
            "received_file": image.filename,
        }
    )


@ai_bp.post("/itinerary/generate")
def generate_itinerary_endpoint():
    """LangGraph multi-agent itinerary generation."""
    body = request.get_json(silent=True) or {}
    start_date = body.get("start_date", "")
    end_date = body.get("end_date", "")
    preferences = body.get("preferences", {})
    
    try:
        from .planner.graph import generate_itinerary
        items = generate_itinerary(start_date, end_date, preferences)
        return jsonify({"items": items})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500


@ai_bp.post("/generate-pdf-summary")
def generate_pdf_summary():
    """Generates a markdown summary of a finalized itinerary for PDF export."""
    body = request.get_json(silent=True) or {}
    itinerary_id = body.get("itinerary_id")
    
    if not itinerary_id:
        return jsonify({"error": "itinerary_id is required"}), 400
        
    from ..models import db, Itinerary
    itinerary = Itinerary.query.get(itinerary_id)
    
    if not itinerary:
        return jsonify({"error": "Itinerary not found"}), 404
        
    try:
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import SystemMessage, HumanMessage
        import os
        
        OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
        if not OPENAI_API_KEY:
            return jsonify({"error": "OPENAI_API_KEY is missing in .env"}), 500
            
        llm = ChatOpenAI(model="gpt-4o", api_key=OPENAI_API_KEY, temperature=0.5)
        
        items = sorted(itinerary.items, key=lambda x: (x.day_number, x.id))
        
        start = itinerary.start_date or "TBD"
        end = itinerary.end_date or "TBD"
        itinerary_text = f"Trip: {itinerary.title}\nDates: {start} to {end}\n\n"
        
        current_day = 0
        for item in items:
            if item.day_number != current_day:
                current_day = item.day_number
                itinerary_text += f"\nDay {current_day}:\n"
            
            attraction_name = item.attraction.name if item.attraction else "Unknown Place"
            itinerary_text += f"- {attraction_name}\n"
            
        system_prompt = """You are a professional travel document generator. 
The user has finalized their trip and wants a beautiful Markdown document that they can download as a PDF.
Write a 1-page summary of the itinerary provided.
Do NOT include the main Trip Name as a heading. Start directly with:
## Trip Summary (Dates, total places)
## Day-by-Day Itinerary (add brief engaging descriptions of each place based on your general knowledge. Use bullet points.)
## Practical Tips (a few general travel tips for this route)

Do not use conversational filler. Just return the markdown."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=itinerary_text)
        ]
        
        response = llm.invoke(messages)
        return jsonify({"markdown": response.content})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

