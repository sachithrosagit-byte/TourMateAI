from app import create_app
from app.extensions import db
from app.models import Hotel

app = create_app()

hotels_data = [
    # Galle
    {"name": "Galle Fort Hotel", "location": "Galle", "latitude": 6.0279, "longitude": 80.2173, "budget_tier": "luxury", "avg_rating": 4.8, "description": "Luxury heritage hotel inside Galle Fort."},
    {"name": "Le Grand Galle", "location": "Galle", "latitude": 6.0315, "longitude": 80.2144, "budget_tier": "luxury", "avg_rating": 4.7, "description": "High-end resort overlooking the ocean and fort."},
    {"name": "The Heritage Hotel", "location": "Galle", "latitude": 6.0261, "longitude": 80.2172, "budget_tier": "mid-range", "avg_rating": 4.3, "description": "Comfortable stay inside the historic Galle Fort."},
    {"name": "Sea View Hostel Galle", "location": "Galle", "latitude": 6.0333, "longitude": 80.2166, "budget_tier": "budget", "avg_rating": 4.0, "description": "Affordable backpacker friendly stay near the beach."},
    
    # Matara
    {"name": "Amaloh Boutique Resort", "location": "Matara", "latitude": 5.9408, "longitude": 80.5363, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Beautiful boutique resort in Polhena."},
    {"name": "Beachway Guesthouse", "location": "Matara", "latitude": 5.9472, "longitude": 80.5483, "budget_tier": "mid-range", "avg_rating": 4.2, "description": "Cozy guesthouse right on the beach."},
    {"name": "Blue Coral Inn", "location": "Matara", "latitude": 5.9421, "longitude": 80.5375, "budget_tier": "budget", "avg_rating": 4.1, "description": "Budget-friendly inn for surfers and travelers."},

    # Ella
    {"name": "98 Acres Resort & Spa", "location": "Ella", "latitude": 6.8643, "longitude": 81.0494, "budget_tier": "luxury", "avg_rating": 4.9, "description": "Stunning resort offering spectacular views of Ella Gap."},
    {"name": "Ella Flower Garden Resort", "location": "Ella", "latitude": 6.8687, "longitude": 81.0505, "budget_tier": "mid-range", "avg_rating": 4.5, "description": "Beautiful garden resort near Little Adam's Peak."},
    {"name": "Ella Rock House", "location": "Ella", "latitude": 6.8741, "longitude": 81.0475, "budget_tier": "budget", "avg_rating": 4.2, "description": "Simple and clean accommodation for hikers."},

    # Nuwara Eliya
    {"name": "The Grand Hotel", "location": "Nuwara Eliya", "latitude": 6.9733, "longitude": 80.7677, "budget_tier": "luxury", "avg_rating": 4.7, "description": "Historic colonial-era luxury hotel."},
    {"name": "Araliya Green Hills", "location": "Nuwara Eliya", "latitude": 6.9691, "longitude": 80.7712, "budget_tier": "mid-range", "avg_rating": 4.4, "description": "Comfortable 4-star hotel in the city center."},
    {"name": "Alpine Hotel", "location": "Nuwara Eliya", "latitude": 6.9680, "longitude": 80.7666, "budget_tier": "budget", "avg_rating": 4.0, "description": "Affordable stay with basic amenities."},

    # Kandy
    {"name": "Earl's Regency", "location": "Kandy", "latitude": 7.2889, "longitude": 80.6552, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Luxury 5-star hotel near the Mahaweli River."},
    {"name": "OZO Kandy", "location": "Kandy", "latitude": 7.2931, "longitude": 80.6385, "budget_tier": "mid-range", "avg_rating": 4.5, "description": "Modern hotel overlooking Kandy Lake."},
    {"name": "Kandy City Hostel", "location": "Kandy", "latitude": 7.2982, "longitude": 80.6358, "budget_tier": "budget", "avg_rating": 4.1, "description": "Popular hostel for budget backpackers."},

    # Anuradhapura
    {"name": "Uga Ulagalla", "location": "Anuradhapura", "latitude": 8.2146, "longitude": 80.5215, "budget_tier": "luxury", "avg_rating": 4.8, "description": "Luxury eco-resort spread over a vast estate."},
    {"name": "Rajarata Hotel", "location": "Anuradhapura", "latitude": 8.3283, "longitude": 80.4072, "budget_tier": "mid-range", "avg_rating": 4.3, "description": "Comfortable hotel close to the ancient city."},
    {"name": "Milano Tourist Rest", "location": "Anuradhapura", "latitude": 8.3371, "longitude": 80.4143, "budget_tier": "budget", "avg_rating": 4.1, "description": "Friendly family-run guesthouse."},

    # Jaffna
    {"name": "Jetwing Jaffna", "location": "Jaffna", "latitude": 9.6640, "longitude": 80.0152, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Prominent luxury hotel in the heart of Jaffna city."},
    {"name": "Tilko Jaffna City Hotel", "location": "Jaffna", "latitude": 9.6631, "longitude": 80.0117, "budget_tier": "mid-range", "avg_rating": 4.0, "description": "Standard hotel offering good city access."},
    {"name": "Yaal Hostel", "location": "Jaffna", "latitude": 9.6698, "longitude": 80.0163, "budget_tier": "budget", "avg_rating": 4.2, "description": "Great budget hostel for exploring the north."},
]

with app.app_context():
    print("Clearing existing hotels...")
    db.session.query(Hotel).delete()
    
    print("Seeding new hotels...")
    for data in hotels_data:
        hotel = Hotel(**data)
        db.session.add(hotel)
        
    db.session.commit()
    print("Successfully seeded hotels!")
