// Personalized recommendations for the Dashboard.
//
// Currently backed by the placeholder GET /api/recommendations/mock (simple
// interest filtering — see backend/app/routes/recommendations.py). When the
// real engine ships (Feature 3.x, POST /api/ai/recommend), only this function's
// endpoint/verb should need to change: the response items already carry the
// contract's { score, reason } alongside full attraction fields.

import api from './api'

export async function fetchRecommendations({ limit = 8 } = {}) {
  const { data } = await api.get('/recommendations', { params: { limit } })
  return data.recommendations // [{ ...attraction, score, reason }]
}
