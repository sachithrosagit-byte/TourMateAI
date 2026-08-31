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

    # Hikkaduwa (approx. town centre: 6.1391, 80.1000 — offsets below are illustrative, not geocoded)
    {"name": "DORMERO Hotel Sri Lanka Hikkaduwa Beach", "location": "Hikkaduwa", "latitude": 6.1405, "longitude": 80.0989, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Beachfront 5-star hotel with outdoor pool and fitness center."},
    {"name": "Hikka Tranz by Cinnamon", "location": "Hikkaduwa", "latitude": 6.1378, "longitude": 80.1012, "budget_tier": "luxury", "avg_rating": 4.4, "description": "4-star eco-friendly beachside resort along Hikkaduwa's shoreline."},
    {"name": "Coral Sands Hotel", "location": "Hikkaduwa", "latitude": 6.1360, "longitude": 80.0975, "budget_tier": "mid-range", "avg_rating": 4.0, "description": "Centrally located hotel on Galle Road, close to Hikkaduwa's main beach strip."},
    {"name": "Villa ArthurCC", "location": "Hikkaduwa", "latitude": 6.1340, "longitude": 80.0958, "budget_tier": "budget", "avg_rating": 4.1, "description": "Guesthouse near Narigama beach with garden and private parking."},

    # Negombo (approx. town centre: 7.2086, 79.8358)
    {"name": "Jetwing Lagoon Wellness, A Luxury Reserve", "location": "Negombo", "latitude": 7.1731, "longitude": 79.8523, "budget_tier": "luxury", "avg_rating": 4.7, "description": "Luxury wellness-focused resort set beside Negombo Lagoon."},
    {"name": "Jetwing Blue", "location": "Negombo", "latitude": 7.2140, "longitude": 79.8365, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Beachfront resort known for understated luxury and coastal views."},
    {"name": "Belmont Boutique Hotel", "location": "Negombo", "latitude": 7.2098, "longitude": 79.8372, "budget_tier": "mid-range", "avg_rating": 4.4, "description": "Boutique hotel praised for warm hospitality and beautifully designed rooms."},
    {"name": "Cloud 9 Hotel", "location": "Negombo", "latitude": 7.2050, "longitude": 79.8340, "budget_tier": "budget", "avg_rating": 4.0, "description": "Popular budget-friendly stay convenient for early flights out of Colombo airport."},

    # Arugam Bay (approx. town centre: 6.8404, 81.8360)
    {"name": "Jetwing Surf & Safari", "location": "Arugam Bay", "latitude": 6.8290, "longitude": 81.8420, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Luxury surf-and-safari lodge on Sri Lanka's east coast."},
    {"name": "Paddyway Resort", "location": "Arugam Bay", "latitude": 6.8425, "longitude": 81.8355, "budget_tier": "mid-range", "avg_rating": 4.5, "description": "Quiet resort just off the main street, a short walk from the beach."},
    {"name": "Sandy Beach Hotel", "location": "Arugam Bay", "latitude": 6.8380, "longitude": 81.8390, "budget_tier": "mid-range", "avg_rating": 4.3, "description": "Beachfront hotel with a restaurant on the sand beneath palm trees."},
    {"name": "Wanderlust Inn", "location": "Arugam Bay", "latitude": 6.8410, "longitude": 81.8340, "budget_tier": "budget", "avg_rating": 4.4, "description": "Backpacker-friendly inn less than a minute's walk from the beach."},

    # Kataragama (approx. town centre: 6.4128, 81.3353)
    {"name": "Mandara Rosen Yala", "location": "Kataragama", "latitude": 6.4085, "longitude": 81.3410, "budget_tier": "luxury", "avg_rating": 4.5, "description": "4-star hotel blending business and spa amenities near Kataragama Temple and Yala."},
    {"name": "Grand Tamarind Lake", "location": "Kataragama", "latitude": 6.4150, "longitude": 81.3320, "budget_tier": "mid-range", "avg_rating": 4.2, "description": "Lakeside hotel offering a peaceful base for temple and safari visits."},
    {"name": "Ekho Safari Tissa", "location": "Kataragama", "latitude": 6.4170, "longitude": 81.3290, "budget_tier": "mid-range", "avg_rating": 4.1, "description": "Comfortable stay geared toward travelers arranging Yala safaris."},
    {"name": "Hotel Senora", "location": "Kataragama", "latitude": 6.4110, "longitude": 81.3370, "budget_tier": "budget", "avg_rating": 3.9, "description": "Affordable hotel with parking, popular with pilgrims visiting Kataragama Temple."},

    # Colombo
    {"name": "Shangri-La Colombo", "location": "Colombo", "latitude": 6.9319, "longitude": 79.8478, "budget_tier": "luxury", "avg_rating": 4.8, "description": "Iconic beachfront luxury hotel in the heart of the city."},
    {"name": "Cinnamon Grand Colombo", "location": "Colombo", "latitude": 6.9184, "longitude": 79.8489, "budget_tier": "luxury", "avg_rating": 4.7, "description": "Premier 5-star hotel known for its dining and central location."},
    {"name": "Galle Face Hotel", "location": "Colombo", "latitude": 6.9226, "longitude": 79.8437, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Historic colonial-era hotel overlooking the Galle Face Green and ocean."},
    {"name": "Hilton Colombo", "location": "Colombo", "latitude": 6.9335, "longitude": 79.8452, "budget_tier": "luxury", "avg_rating": 4.6, "description": "Modern high-rise hotel with panoramic city and harbour views."},
    {"name": "OZO Colombo", "location": "Colombo", "latitude": 6.9147, "longitude": 79.8590, "budget_tier": "mid-range", "avg_rating": 4.4, "description": "Contemporary hotel popular with business and leisure travelers."},
    {"name": "Cinnamon Red Colombo", "location": "Colombo", "latitude": 6.9151, "longitude": 79.8497, "budget_tier": "mid-range", "avg_rating": 4.3, "description": "Trendy mid-range hotel close to Colombo City Centre mall."},
    {"name": "Tintagel Colombo", "location": "Colombo", "latitude": 6.9012, "longitude": 79.8562, "budget_tier": "mid-range", "avg_rating": 4.5, "description": "Boutique heritage hotel with a notable historical past."},
    {"name": "Ramada Colombo", "location": "Colombo", "latitude": 6.9358, "longitude": 79.8442, "budget_tier": "mid-range", "avg_rating": 4.2, "description": "Comfortable seafront hotel with easy access to Galle Face."},
    {"name": "Colombo City Hostel", "location": "Colombo", "latitude": 6.9271, "longitude": 79.8612, "budget_tier": "budget", "avg_rating": 4.1, "description": "Popular backpacker hostel near Fort and the railway station."},
    {"name": "Clock Inn Colombo", "location": "Colombo", "latitude": 6.9147, "longitude": 79.8483, "budget_tier": "budget", "avg_rating": 4.0, "description": "Affordable, well-located hostel favored by solo travelers."},
    {"name": "Ottery Tourist Home", "location": "Colombo", "latitude": 6.8952, "longitude": 79.8570, "budget_tier": "budget", "avg_rating": 3.9, "description": "Simple guesthouse offering good value near Bambalapitiya."},
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