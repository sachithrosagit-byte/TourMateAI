// Itinerary API calls (see backend/app/routes/itineraries.py for the
// contracts these mirror). Detail responses include `items` with each
// attraction expanded, ordered by (day_number, order_index) — ready to group
// by day and render.

import api from './api'

export async function fetchItineraries() {
  const { data } = await api.get('/itineraries')
  return data.itineraries // [{ id, title, start_date, end_date, item_count, preview_stops }]
}

export async function createItinerary({ title, description, startLocation, endLocation, stops, startDate, endDate, is_ai_generated, tripType }) {
  const { data } = await api.post('/itineraries', {
    title,
    description,
    start_location: startLocation || null,
    end_location: endLocation || null,
    stops: stops || [],
    start_date: startDate || null,
    end_date: endDate || null,
    is_ai_generated: is_ai_generated || false,
    trip_type: tripType || 'Solo',
  })
  return data.itinerary // detail shape (items: [])
}

export async function fetchItinerary(id) {
  const { data } = await api.get(`/itineraries/${id}`)
  return data.itinerary // { ...list fields, items: [{ id, day_number, order_index, attraction }] }
}

// Partial update — only pass the fields that changed.
export async function updateItinerary(id, fields) {
  const { data } = await api.put(`/itineraries/${id}`, fields)
  return data.itinerary
}

export async function deleteItinerary(id) {
  const { data } = await api.delete(`/itineraries/${id}`)
  return data.deleted
}

export async function addItineraryItem(id, { attractionId, hotelId, dayNumber }) {
  const payload = { day_number: dayNumber }
  if (attractionId) payload.attraction_id = attractionId
  if (hotelId) payload.hotel_id = hotelId

  const { data } = await api.post(`/itineraries/${id}/items`, payload)
  return data.item
}

// `itemIds` is the complete new order for that day.
export async function reorderItineraryItems(id, dayNumber, itemIds) {
  const { data } = await api.put(`/itineraries/${id}/items/reorder`, {
    day_number: dayNumber,
    item_ids: itemIds,
  })
  return data.itinerary
}

export async function removeItineraryItem(id, itemId) {
  const { data } = await api.delete(`/itineraries/${id}/items/${itemId}`)
  return data.deleted
}

// Driving route through one day's located stops, in their current order —
// { route: { total_distance_m, total_duration_s, legs }, stops }. With
// optimize: true the response adds `suggested_item_order` (located item ids
// in Google's travel-minimising order; first/last stay fixed) and the route
// totals describe that suggested order. 400 when the day has fewer than two
// located stops; 503 (rejected promise) when routing is unavailable — callers
// should catch and degrade gracefully.
export async function fetchDayRoute(id, dayNumber, { optimize = false } = {}) {
  const { data } = await api.get(
    `/itineraries/${id}/days/${dayNumber}/route${optimize ? '?optimize=true' : ''}`
  )
  return data
}

// LangGraph AI Auto-Generation
export async function generateItineraryWithAI({ startDate, endDate, preferences }) {
  const { data } = await api.post('/ai/itinerary/generate', {
    start_date: startDate,
    end_date: endDate,
    preferences,
  })
  return data.items
}
