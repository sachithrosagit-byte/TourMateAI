from typing import TypedDict, Annotated, List, Dict, Any
import operator

class PlannerState(TypedDict):
    """The state of the itinerary planning graph."""
    start_date: str
    end_date: str
    preferences: Dict[str, Any]
    
    # Intent extraction fields
    start_lat: float
    start_lng: float
    target_lat: float
    target_lng: float
    waypoints: list[dict] # [{"lat": lat, "lng": lng, "name": name}]
    radius_km: float
    refined_interests: list[str]
    
    # Existing fields
    context: Dict[str, Any]
    candidate_attractions: list[Dict[str, Any]]
    itinerary_items: list[Dict[str, Any]] # e.g., [{"day_number": 1, "attraction_id": 7, "order": 1}, ...]
    
    # Chat/Logs for debugging or reasoning
    messages: Annotated[list, operator.add]
