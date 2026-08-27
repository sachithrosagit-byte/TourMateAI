// Attraction catalogue API calls (see backend/app/routes/attractions.py and
// interactions.py for the contracts these mirror).

import api from './api'

export async function fetchAttractions({
  search = '',
  category = '',
  sort = 'rating',
  page = 1,
  perPage = 24,
} = {}) {
  const params = { sort, page, per_page: perPage }
  if (search) params.search = search
  if (category) params.category = category
  const { data } = await api.get('/attractions', { params })
  return data // { attractions: [...], pagination: {...} }
}

export async function fetchAttraction(id) {
  const { data } = await api.get(`/attractions/${id}`)
  return data.attraction // includes rating_count + reviews[]
}

export async function submitFeedback(id, { rating, comment }) {
  const { data } = await api.post(`/attractions/${id}/feedback`, {
    rating,
    comment,
  })
  return data // { feedback, attraction_avg_rating }
}

// Fire-and-forget event log — the recommender's training signal. Never let a
// failed log break the browsing experience.
export function logInteraction(attractionId, interactionType) {
  return api
    .post('/interactions', {
      attraction_id: attractionId,
      interaction_type: interactionType,
    })
    .catch(() => {})
}

export async function fetchNearbyAttractions(id) {
  const { data } = await api.get(`/attractions/${id}/nearby`)
  return data.attractions
}
