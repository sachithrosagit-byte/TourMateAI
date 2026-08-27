import logging
from typing import List, Dict, Any, Optional

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.models import Attraction, Interaction, InteractionType
from app.extensions import db
from app.services.weather import get_weather, WeatherUnavailable

logger = logging.getLogger(__name__)

class RecommendationEngine:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(stop_words='english')
        self.tfidf_matrix = None
        self.attraction_ids = []
        self.attractions_df = None
        self._is_fitted = False

    def fit(self):
        """Builds the TF-IDF matrix for all attractions and caches it."""
        logger.info("Fitting RecommendationEngine...")
        attractions = Attraction.query.all()
        if not attractions:
            logger.warning("No attractions found in the database. Engine cannot be fitted.")
            return

        data = []
        for a in attractions:
            # Create a rich metadata 'soup' for TF-IDF
            soup = f"{a.name or ''} {a.category or ''} {a.description or ''}"
            data.append({
                'id': a.id,
                'soup': soup,
                'avg_rating': a.avg_rating or 0.0,
                'latitude': a.latitude,
                'longitude': a.longitude,
                'category': a.category
            })

        self.attractions_df = pd.DataFrame(data)
        self.attraction_ids = self.attractions_df['id'].tolist()
        
        # Fit TF-IDF on the soup
        self.tfidf_matrix = self.vectorizer.fit_transform(self.attractions_df['soup'])
        self._is_fitted = True
        logger.info(f"RecommendationEngine fitted with {len(attractions)} attractions.")

    def _build_user_profile(self, user) -> str:
        """Builds a query string representing the user's preferences."""
        profile_parts = []

        # 1. Explicit Preferences
        if user and user.preferences:
            interests = user.preferences.get("interests", [])
            if interests:
                # Give explicit interests a strong weight by repeating them
                profile_parts.append(" ".join(interests) * 3)

        # 2. Implicit Preferences (Interactions)
        if user:
            # Get user's interactions
            interactions = Interaction.query.filter_by(user_id=user.id).all()
            for interaction in interactions:
                attraction = interaction.attraction
                if attraction:
                    soup = f"{attraction.name or ''} {attraction.category or ''}"
                    if interaction.interaction_type == InteractionType.visit:
                        profile_parts.append(soup * 2)  # High weight for visits
                    elif interaction.interaction_type == InteractionType.like:
                        profile_parts.append(soup * 2)  # High weight for likes
                    elif interaction.interaction_type == InteractionType.view:
                        profile_parts.append(soup)      # Normal weight for views

        return " ".join(profile_parts)

    def get_recommendations(self, user, limit: int = 10, lat: float = None, lng: float = None) -> List[Dict[str, Any]]:
        """Generates personalized recommendations for a user."""
        if not self._is_fitted:
            self.fit()
            if not self._is_fitted:
                return []

        # 1. Build user profile and vectorize
        user_profile_text = self._build_user_profile(user)
        
        # If no profile at all, we could just return top rated
        if not user_profile_text.strip():
            # Fallback to popular items if no profile
            return self._get_popular_recommendations(limit)

        user_vector = self.vectorizer.transform([user_profile_text])

        # 2. Calculate Cosine Similarity
        cosine_sim = cosine_similarity(user_vector, self.tfidf_matrix).flatten()

        # 3. Apply base modifiers (rating)
        scores = []
        for idx, sim_score in enumerate(cosine_sim):
            attraction_row = self.attractions_df.iloc[idx]
            final_score = float(sim_score)
            
            # Modifier 1: Average Rating (slight boost)
            avg_rating = attraction_row['avg_rating']
            if avg_rating > 0:
                final_score += (avg_rating / 5.0) * 0.1  # Max 10% boost for 5 stars

            scores.append((idx, attraction_row['id'], final_score))

        # 4. Sort by base score descending
        scores.sort(key=lambda x: x[2], reverse=True)
        
        # 5. Apply expensive modifiers (Weather) only to top contenders
        # We take 2x the limit so we have room to penalize and re-sort
        top_contenders = scores[:limit * 2]
        final_scores = []
        
        for idx, att_id, score in top_contenders:
            attraction_row = self.attractions_df.iloc[idx]
            
            # Modifier 2: Weather (if location provided)
            if lat is not None and lng is not None and attraction_row['latitude'] and attraction_row['longitude']:
                 outdoor_categories = ['Beach', 'Wildlife', 'Nature', 'Park', 'Ruins']
                 if any(cat in str(attraction_row['category']) for cat in outdoor_categories):
                     try:
                         weather_data = get_weather(attraction_row['latitude'], attraction_row['longitude'])
                         if weather_data.get('current', {}).get('is_bad', False):
                             # 30% penalty for bad weather
                             score *= 0.70
                     except WeatherUnavailable:
                         pass

            final_scores.append((att_id, score))

        # Re-sort after weather penalty
        final_scores.sort(key=lambda x: x[1], reverse=True)
        top_ids_and_scores = final_scores[:limit]
        
        # 6. Fetch actual attraction objects
        recommended_attractions = []
        for att_id, score_val in top_ids_and_scores:
            att = Attraction.query.get(att_id)
            if att:
                recommended_attractions.append({
                    "attraction": att,
                    "score": round(score_val, 4)
                })

        return recommended_attractions

    def _get_popular_recommendations(self, limit: int) -> List[Dict[str, Any]]:
        """Fallback for cold-start (no user profile)."""
        top_attractions = Attraction.query.order_by(Attraction.avg_rating.desc()).limit(limit).all()
        return [{"attraction": att, "score": 1.0} for att in top_attractions]

# Global instance
recommendation_engine = RecommendationEngine()
