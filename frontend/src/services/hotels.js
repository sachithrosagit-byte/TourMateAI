import api from './api'

export async function fetchHotels({
  search = '',
  budgetTier = '',
  location = '',
  sort = 'rating',
  page = 1,
  perPage = 24,
} = {}) {
  const params = { sort_by: sort, page, per_page: perPage }
  if (search) params.search = search
  if (budgetTier) params.budget_tier = budgetTier
  if (location) params.location = location
  
  const { data } = await api.get('/hotels', { params })
  return data // { hotels: [...], total: ..., pages: ..., current_page: ... }
}

export async function fetchHotel(id) {
  const { data } = await api.get(`/hotels/${id}`)
  return data.hotel
}
