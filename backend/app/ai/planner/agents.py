import os
import json
import logging
import math
import re
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from .state import PlannerState
from app.models import Attraction, Hotel

logger = logging.getLogger(__name__)

def get_llm():
    """Get the LLM instance. Make sure GEMINI_API_KEY is in environment or .env"""
    # Assuming the app has loaded the .env file
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.warning("GEMINI_API_KEY is not set. Using dummy key to prevent ADC hang.")
        api_key = "dummy_key_to_prevent_adc_hang"
    return ChatGoogleGenerativeAI(model="gemini-3.6-flash", api_key=api_key)

def context_agent(state: PlannerState) -> PlannerState:
    """Gathers context like weather based on dates."""
    # In a real app, call fetchWeather() here.
    # For now, return a generic sunny context.
    logger.info("Running context_agent")
    return {"weather_context": {"summary": "Generally sunny, good for outdoor activities."}}

def haversine_distance(lat1, lon1, lat2, lon2):
    """Calculate the great circle distance in kilometers between two points on the earth."""
    if None in (lat1, lon1, lat2, lon2):
        return float('inf')
    R = 6371.0 # Earth radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

import requests

def geocode_location(location_name: str, default_lat: float, default_lng: float):
    if not location_name or not location_name.strip():
        return default_lat, default_lng
    search_query = f"{location_name.strip()}, Sri Lanka"
    geo_url = f"https://nominatim.openstreetmap.org/search?q={search_query}&format=json&limit=1"
    headers = {'User-Agent': 'TourMateAI/1.0'}
    try:
        geo_resp = requests.get(geo_url, headers=headers, timeout=10)
        if geo_resp.status_code == 200:
            geo_data = geo_resp.json()
            if geo_data and len(geo_data) > 0:
                return float(geo_data[0].get("lat", default_lat)), float(geo_data[0].get("lon", default_lng))
    except Exception as e:
        logger.error(f"Geocode failed for {location_name}: {e}")
    return default_lat, default_lng

def intent_agent(state: PlannerState) -> PlannerState:
    """Extracts geographic intent and refined interests from user description using OpenStreetMap Geocoding."""
    logger.info("Running intent_agent")
    llm = get_llm()
    preferences = state.get("preferences", {})
    description = preferences.get("description", "")
    start_loc_pref = preferences.get("start_location", "")
    end_loc_pref = preferences.get("end_location", "")
    stops_pref = preferences.get("stops", [])
    trip_type = preferences.get("trip_type", "Solo")
    
    # Base defaults
    target_lat, target_lng = 7.8731, 80.7718
    start_lat, start_lng = None, None
    radius_km = 500.0
    refined_interests = ["General tourism"]
    waypoints = []
    
    # Geocode explicit start
    if start_loc_pref:
        start_lat, start_lng = geocode_location(start_loc_pref, target_lat, target_lng)
        logger.info(f"Geocoded From: {start_loc_pref} to {start_lat}, {start_lng}")
        
    # Geocode stops
    for stop in stops_pref:
        if stop and stop.strip():
            slat, slng = geocode_location(stop, target_lat, target_lng)
            waypoints.append({"name": stop, "lat": slat, "lng": slng})
            logger.info(f"Geocoded Stop: {stop} to {slat}, {slng}")
        
    # Geocode explicit end
    if end_loc_pref:
        target_lat, target_lng = geocode_location(end_loc_pref, target_lat, target_lng)
        waypoints.append({"name": end_loc_pref, "lat": target_lat, "lng": target_lng})
        logger.info(f"Geocoded To: {end_loc_pref} to {target_lat}, {target_lng}")
        radius_km = 100.0

    # Ask LLM to refine interests from description, and possibly guess location if 'To' was empty
    if description or trip_type:
        prompt = f"""
        You are a travel assistant for a Sri Lanka travel app.
        Analyze the following user trip description: "{description}"
        The user is planning a {trip_type} trip. When refining their interests, strictly factor this in (e.g., if 'Family', include kid-friendly; if 'Couple', include romantic, if 'Solo', include backpacking/adventure/safety).
        
        Extract:
        1. The specific location name they want to visit (if any). e.g., "Galle", "Kandy", "Dikwella". If none mentioned or if it's already '{end_loc_pref}', return "".
        2. The main interests/activities (e.g., ["sea bath", "sunset", "history"]).
        3. A search radius in km (e.g., 50 for a specific city/beach, 150 for a province, 500 if no location is specified).
        
        Return EXACTLY a JSON object with keys: "location_name" (string), "refined_interests" (list of strings), "radius_km" (float).
        Example: {{"location_name": "Galle", "refined_interests": ["sea bath", "turtles"], "radius_km": 30.0}}
        """
        try:
            response = llm.invoke([HumanMessage(content=prompt)])
            content_str = response.content
            if isinstance(content_str, list):
                content_str = " ".join([str(c) for c in content_str])
            else:
                content_str = str(content_str)
                
            match = re.search(r'\{.*\}', content_str, re.DOTALL)
            if match:
                json_str = match.group(0)
                try:
                    parsed = json.loads(json_str)
                except json.JSONDecodeError:
                    import ast
                    parsed = ast.literal_eval(json_str)
                    
                refined_interests = parsed.get("refined_interests", refined_interests)
                radius_km = float(parsed.get("radius_km", radius_km))
                location_name = parsed.get("location_name", "")
                
                # If they didn't provide an explicit 'To' location, use the LLM's guess
                if not end_loc_pref and location_name and location_name.strip():
                    target_lat, target_lng = geocode_location(location_name, target_lat, target_lng)
                    waypoints.append({"name": location_name, "lat": target_lat, "lng": target_lng})
                    logger.info(f"Geocoded LLM guessed To: {location_name} to {target_lat}, {target_lng}")
        except Exception as e:
            logger.error(f"Failed to parse intent: {e}")

    # Fallback start_lat if not provided
    if start_lat is None:
        start_lat, start_lng = target_lat, target_lng

    return {
        "start_lat": start_lat,
        "start_lng": start_lng,
        "target_lat": target_lat, 
        "target_lng": target_lng,
        "waypoints": waypoints,
        "radius_km": radius_km, 
        "refined_interests": refined_interests
    }

def discovery_agent(state: PlannerState) -> PlannerState:
    """Selects candidate attractions based on geographically filtered places."""
    logger.info("Running discovery_agent")
    llm = get_llm()
    
    start_lat = state.get("start_lat")
    start_lng = state.get("start_lng")
    target_lat = state.get("target_lat", 7.8731)
    target_lng = state.get("target_lng", 80.7718)
    waypoints = state.get("waypoints", [])
    radius_km = state.get("radius_km", 500.0)
    interests = state.get("refined_interests", [])
    trip_type = state.get("preferences", {}).get("trip_type", "Solo")
    
    places = Attraction.query.all()
    all_places = [{"id": p.id, "name": p.name, "category": p.category, "description": p.description, "latitude": p.latitude, "longitude": p.longitude} for p in places]
    
    # Haversine geographic filtering: include if within radius of start, target, or any waypoint
    available_places = []
    for p in all_places:
        min_dist = haversine_distance(target_lat, target_lng, p["latitude"], p["longitude"])
        if start_lat is not None and start_lng is not None:
            min_dist = min(min_dist, haversine_distance(start_lat, start_lng, p["latitude"], p["longitude"]))
        for w in waypoints:
            min_dist = min(min_dist, haversine_distance(w["lat"], w["lng"], p["latitude"], p["longitude"]))
            
        if min_dist <= radius_km:
            available_places.append(p)
            
    if not available_places:
        available_places = all_places
    
    prompt = f"""
    You are a travel recommender for Sri Lanka.
    The user is traveling on a route. Key stops include: {', '.join([w['name'] for w in waypoints]) if waypoints else 'General exploration'}
    
    The user is traveling as a {trip_type}.
    The user is interested in: {', '.join(interests) if interests else 'General tourism'}
    
    Here are the places that are geographically close to their route:
    {json.dumps(available_places, indent=2)}
    
    Select the top places that best match their interests and would make logical stops for this specific type of group ({trip_type}).
    Return ONLY a JSON array of their integer IDs.
    Example: [7, 15, 3]
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        content_str = response.content
        if isinstance(content_str, list):
            content_str = " ".join([str(c) for c in content_str])
        else:
            content_str = str(content_str)
            
        match = re.search(r'\[.*\]', content_str, re.DOTALL)
        if match:
            json_str = match.group(0)
            try:
                selected_ids = json.loads(json_str)
            except json.JSONDecodeError:
                import ast
                selected_ids = ast.literal_eval(json_str)
        else:
            selected_ids = []
            
        candidates = [p for p in available_places if p["id"] in selected_ids]
        if not candidates:
             candidates = available_places[:3] # fallback
    except Exception as e:
        logger.error(f"LLM parsing error in discovery_agent: {e}")
        candidates = available_places[:3] # fallback
        
    return {"candidate_attractions": candidates}

def scheduler_agent(state: PlannerState) -> PlannerState:
    """Distributes attractions across days using waypoint chaining."""
    logger.info("Running waypoint-aware scheduler_agent")
    candidates = state.get("candidate_attractions", [])
    
    current_lat = state.get("start_lat", 7.8731)
    current_lng = state.get("start_lng", 80.7718)
    waypoints = list(state.get("waypoints", []))
    
    start_date = state.get("start_date")
    end_date = state.get("end_date")
    
    total_days = 3
    if start_date and end_date:
        try:
            from datetime import datetime
            d1 = datetime.strptime(start_date, "%Y-%m-%d")
            d2 = datetime.strptime(end_date, "%Y-%m-%d")
            total_days = max(1, (d2 - d1).days + 1)
        except:
            pass
            
    itinerary_items = []
    available = list(candidates)
    
    MAX_PLACES_PER_DAY = 3
    MAX_JUMP_KM = 30.0 # user requested to reduce 50km to 30km
    all_hotels = Hotel.query.all()
    
    for day in range(1, total_days + 1):
        stops_today = 0
        while stops_today < MAX_PLACES_PER_DAY and available:
            
            is_exploring = (len(waypoints) == 0)
            
            def score_place(p):
                dist_from_current = haversine_distance(current_lat, current_lng, p["latitude"], p["longitude"])
                if is_exploring:
                    # If exploring destination, just pick nearest
                    return dist_from_current
                # If en-route, pick places that minimize detour to next waypoint
                dist_to_target = haversine_distance(p["latitude"], p["longitude"], waypoints[0]["lat"], waypoints[0]["lng"])
                return dist_from_current + dist_to_target
                
            available.sort(key=score_place)
            best_place = available[0]
            
            dist_from_current = haversine_distance(current_lat, current_lng, best_place["latitude"], best_place["longitude"])
            
            # Prevent jumping too far at once
            if stops_today > 0 and dist_from_current > MAX_JUMP_KM:
                if len(available) > 1:
                    break
                    
            itinerary_items.append({
                "attraction_id": best_place["id"],
                "day_number": day,
                "order": stops_today + 1,
                "latitude": best_place["latitude"],
                "longitude": best_place["longitude"]
            })
            
            current_lat = best_place["latitude"]
            current_lng = best_place["longitude"]
            
            # Check if we arrived at the current waypoint
            if not is_exploring:
                dist_to_waypoint = haversine_distance(current_lat, current_lng, waypoints[0]["lat"], waypoints[0]["lng"])
                if dist_to_waypoint <= 20.0:
                    logger.info(f"Reached waypoint {waypoints[0].get('name')}")
                    waypoints.pop(0)
            
            available.pop(0)
            stops_today += 1

        # End of day: append the nearest hotel, except on the last day
        if day < total_days and all_hotels:
            nearest_hotel = min(all_hotels, key=lambda h: haversine_distance(current_lat, current_lng, h.latitude, h.longitude))
            itinerary_items.append({
                "hotel_id": nearest_hotel.id,
                "day_number": day,
                "order": stops_today + 1,
                "latitude": nearest_hotel.latitude,
                "longitude": nearest_hotel.longitude
            })
            current_lat = nearest_hotel.latitude
            current_lng = nearest_hotel.longitude
            
    return {"itinerary_items": itinerary_items}

def routing_agent(state: PlannerState) -> PlannerState:
    """Optimizes the order within each day."""
    logger.info("Running routing_agent")
    items = state.get("itinerary_items", [])
    
    # Group by day
    by_day = {}
    for item in items:
        by_day.setdefault(item["day_number"], []).append(item)
        
    # Simple sort by ID or coordinates for now.
    # In a real app, use Google Maps API TSP solver
    optimized_items = []
    for day, day_items in by_day.items():
        for i, item in enumerate(day_items):
            item["order"] = i + 1
            optimized_items.append(item)
            
    return {"itinerary_items": optimized_items}
