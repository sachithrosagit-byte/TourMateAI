// Weather API calls (see backend/app/routes/weather.py). The backend proxies
// OpenWeather and caches results, so it's cheap to call per attraction/day.

import api from './api'

// Resolves to { current, forecast: [{date, is_bad, ...}], available, ... }.
// On an upstream/config failure the backend answers 503, which surfaces here as
// a rejected promise — callers should catch it and show a friendly fallback.
export async function fetchWeather(lat, lng) {
  const { data } = await api.get(`/weather/${lat}/${lng}`)
  return data
}
