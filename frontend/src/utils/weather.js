// Shared weather presentation helpers (used by the itinerary planner). Maps an
// OpenWeather "main" condition to an emoji so widgets stay self-contained and
// never depend on loading a remote icon.

const EMOJI = {
  Clear: '☀️',
  Clouds: '☁️',
  Rain: '🌧️',
  Drizzle: '🌦️',
  Thunderstorm: '⛈️',
  Snow: '❄️',
  Mist: '🌫️',
  Fog: '🌫️',
  Haze: '🌫️',
  Smoke: '🌫️',
  Dust: '🌫️',
  Squall: '💨',
  Tornado: '🌪️',
}

export function weatherEmoji(condition) {
  return EMOJI[condition] || '🌡️'
}
