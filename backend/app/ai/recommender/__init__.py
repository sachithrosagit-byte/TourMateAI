from .engine import recommendation_engine

def recommend(user_id: int, limit: int = 10, lat: float = None, lng: float = None):
    """
    Returns personalized recommendations.
    Provides a list of dicts with full serialized attraction + score & reason.
    """
    from app.models import User
    from app.routes.attractions import _serialize_attraction
    
    user = User.query.get(user_id) if user_id else None
    
    # We call the engine
    results = recommendation_engine.get_recommendations(user=user, limit=limit, lat=lat, lng=lng)
    
    formatted_results = []
    for res in results:
        att = res['attraction']
        score = res['score']
        
        # Determine the reason
        reason = "Popular with travelers across Sri Lanka"
        if user and user.preferences:
            interests = user.preferences.get("interests", [])
            if att.category in interests:
                reason = f"Matches your interest in {att.category}"
            elif score > 0.5: # heuristic for similarity driven by implicit interaction
                reason = "Based on places you've liked or visited"
                
        data = _serialize_attraction(att)
        data["score"] = score
        data["reason"] = reason
        formatted_results.append(data)
        
    return formatted_results
