// Current-user profile API calls (see backend/app/routes/users.py). Every
// endpoint here acts on the logged-in user — the backend resolves them from the
// Firebase token attached by the Axios interceptor, so no id is ever sent.

import api from './api'

// The travel-preference options the Profile form offers. INTERESTS mirrors the
// backend's INTEREST_OPTIONS (which equal the Attraction categories), so what a
// user picks maps straight onto attractions for the recommender.
export const INTERESTS = [
  'Heritage',
  'Religious',
  'Historical',
  'Scenic',
  'Wildlife',
  'Hiking',
  'Hill Country',
  'Beach',
  'Nature',
]

export const BUDGET_OPTIONS = [
  { value: 'low', label: 'Budget' },
  { value: 'medium', label: 'Mid-range' },
  { value: 'high', label: 'Luxury' },
]

export const PACE_OPTIONS = [
  { value: 'relaxed', label: 'Relaxed — a few stops, plenty of downtime' },
  { value: 'moderate', label: 'Moderate — a comfortable balance' },
  { value: 'packed', label: 'Packed — see as much as possible' },
]

export async function fetchMyProfile() {
  const { data } = await api.get('/users/me')
  return data.user
}

export async function updateMyProfile({ name, preferences }) {
  const { data } = await api.put('/users/me', { name, preferences })
  return data.user // the updated user row
}

export async function fetchMyFeedback() {
  const { data } = await api.get('/users/me/feedback')
  return data.feedback // [{ id, attraction_id, attraction_name, rating, comment, ... }]
}
