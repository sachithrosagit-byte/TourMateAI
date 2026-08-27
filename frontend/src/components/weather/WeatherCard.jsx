// Weather card for a coordinate — current conditions up top (temp, feels-like,
// humidity, wind) and a compact 5-day forecast strip below. Fetches once per
// lat/lng from the backend proxy and degrades to a quiet note when weather is
// unavailable (missing key upstream, rate limit, …) instead of breaking.

import { useEffect, useState } from 'react'
import { fetchWeather } from '../../services/weather'
import { weatherEmoji } from '../../utils/weather'
import '../../styles/weather.css'

function forecastDayLabel(iso, index) {
  if (index === 0) return 'Today'
  return new Date(`${iso}T12:00:00Z`).toLocaleDateString(undefined, {
    weekday: 'short',
    timeZone: 'UTC',
  })
}

function capitalize(text) {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : ''
}

export default function WeatherCard({ latitude, longitude, placeName }) {
  const hasCoords = typeof latitude === 'number' && typeof longitude === 'number'
  const [state, setState] = useState('loading') // loading | ok | unavailable
  const [weather, setWeather] = useState(null)

  useEffect(() => {
    if (!hasCoords) {
      setState('unavailable')
      return undefined
    }
    let cancelled = false
    setState('loading')
    fetchWeather(latitude, longitude)
      .then((data) => {
        if (cancelled) return
        if (data.available === false || !data.current) {
          setState('unavailable')
        } else {
          setWeather(data)
          setState('ok')
        }
      })
      .catch(() => {
        if (!cancelled) setState('unavailable')
      })
    return () => {
      cancelled = true
    }
  }, [latitude, longitude, hasCoords])

  if (state === 'loading') {
    return (
      <div className="weather-card" aria-busy="true" aria-label="Loading weather">
        <div className="skeleton weather-skeleton-now" />
        <div className="skeleton weather-skeleton-strip" />
      </div>
    )
  }

  if (state === 'unavailable') {
    return (
      <p className="weather-unavailable">
        Live weather isn’t available right now — check back shortly.
      </p>
    )
  }

  const { current, forecast } = weather
  const days = (forecast || []).slice(0, 5)

  return (
    <div className="weather-card">
      <div className="weather-now">
        <span className="weather-now-emoji" aria-hidden="true">
          {weatherEmoji(current.condition)}
        </span>
        <div className="weather-now-main">
          <span className="weather-now-temp">
            {typeof current.temp_c === 'number' ? `${Math.round(current.temp_c)}°C` : '—'}
          </span>
          <span className="weather-now-desc">
            {capitalize(current.description) || current.condition}
            {placeName ? ` in ${placeName}` : ''}
          </span>
        </div>
      </div>

      <dl className="weather-now-facts">
        {typeof current.feels_like_c === 'number' && (
          <div className="weather-fact">
            <dt>Feels like</dt>
            <dd>{Math.round(current.feels_like_c)}°C</dd>
          </div>
        )}
        {typeof current.humidity === 'number' && (
          <div className="weather-fact">
            <dt>Humidity</dt>
            <dd>{current.humidity}%</dd>
          </div>
        )}
        {typeof current.wind_kmh === 'number' && (
          <div className="weather-fact">
            <dt>Wind</dt>
            <dd>{Math.round(current.wind_kmh)} km/h</dd>
          </div>
        )}
      </dl>

      {days.length > 0 && (
        <ol className="weather-strip" aria-label="5-day forecast">
          {days.map((day, index) => (
            <li
              key={day.date}
              className={`weather-strip-day${day.is_bad ? ' is-bad' : ''}`}
              title={capitalize(day.description) || day.condition}
            >
              <span className="weather-strip-label">
                {forecastDayLabel(day.date, index)}
              </span>
              <span className="weather-strip-emoji" aria-hidden="true">
                {weatherEmoji(day.condition)}
              </span>
              <span className="weather-strip-temps">
                {typeof day.temp_max_c === 'number' && (
                  <strong>{Math.round(day.temp_max_c)}°</strong>
                )}
                {typeof day.temp_min_c === 'number' && (
                  <span className="weather-strip-min">{Math.round(day.temp_min_c)}°</span>
                )}
              </span>
              {typeof day.rain_chance === 'number' && day.rain_chance >= 20 && (
                <span className="weather-strip-rain">💧 {day.rain_chance}%</span>
              )}
            </li>
          ))}
        </ol>
      )}
    </div>
  )
}
