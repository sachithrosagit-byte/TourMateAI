// Itinerary Builder — plan one trip day by day. A photo "trip cover" hero up
// top (title + dates auto-saved, with a status chip), a sticky day-strip
// navigator that shows the whole trip's shape (per-day stop density + weather
// once checked), and a vertical day-by-day timeline where each day takes
// attractions from the search picker, supports drag-to-reorder within the day
// (FLIP-animated so rows glide instead of jump), and item removal. Each day
// with 2+ located stops shows a live driving route summary and, with enough
// stops, an "Optimize order" suggestion. A sticky summary rail keeps trip
// totals in view and hosts the weather-aware suggestions button, which flags
// rainy days as a planning nudge. On narrow viewports the timeline collapses
// to one day at a time, navigated by the day strip / prev-next controls.

import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { Link, useParams, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import AttractionImage from '../components/explore/AttractionImage'
import AttractionPicker from '../components/itinerary/AttractionPicker'
import { attractionPhoto, scenes } from '../assets/photos'
import TripMapCard from '../components/itinerary/TripMapCard'
import {
  addItineraryItem,
  fetchDayRoute,
  fetchItinerary,
  removeItineraryItem,
  reorderItineraryItems,
  updateItinerary,
  generateItineraryWithAI,
} from '../services/itineraries'
import { fetchWeather } from '../services/weather'
import { dayCount, dayDateLabel, dayIsoDate, formatTripRange } from '../utils/tripDates'
import { weatherEmoji } from '../utils/weather'
import '../styles/itinerary.css'

function DragHandleIcon() {
  return (
    <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
      <circle cx="9" cy="6" r="1.6" />
      <circle cx="15" cy="6" r="1.6" />
      <circle cx="9" cy="12" r="1.6" />
      <circle cx="15" cy="12" r="1.6" />
      <circle cx="9" cy="18" r="1.6" />
      <circle cx="15" cy="18" r="1.6" />
    </svg>
  )
}

/** One attraction row inside a day — draggable, removable, links to detail. */
function DayItemRow({ item, dragging, onDragStart, onDragEnter, onDragEnd, onRemove }) {
  const { t } = useTranslation()
  const attraction = item.attraction
  const hotel = item.hotel
  return (
    <div
      className={`it-item ${dragging ? 'it-item-dragging' : ''}`}
      data-flip-id={item.id}
      draggable
      onDragStart={(e) => {
        e.dataTransfer.effectAllowed = 'move'
        e.dataTransfer.setData('text/plain', String(item.id))
        onDragStart(item)
      }}
      onDragEnter={() => onDragEnter(item)}
      onDragOver={(e) => e.preventDefault()}
      onDragEnd={onDragEnd}
      onDrop={(e) => e.preventDefault()}
    >
      <span className="it-item-handle" title={t('itineraryBuilder.dragToReorder')} aria-hidden="true">
        <DragHandleIcon />
      </span>
      <div className="it-item-thumb">
        {attraction ? (
          <AttractionImage attraction={attraction} className="it-item-img" />
        ) : hotel ? (
          <img src={hotel.image_url || 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=800'} alt={hotel.name} className="it-item-img" style={{ objectFit: 'cover' }} />
        ) : (
          <div className="it-item-img it-item-img-missing" />
        )}
      </div>
      <div className="it-item-body">
        {attraction ? (
          <Link to={`/explore/${attraction.id}`} className="it-item-name">
            {attraction.name}
          </Link>
        ) : hotel ? (
          <span className="it-item-name">
            {hotel.name} <span style={{fontSize: '0.85em', color: '#666', fontWeight: 'normal', marginLeft: '4px'}}>· {t('itineraryBuilder.hotelLabel')}</span>
          </span>
        ) : (
          <span className="it-item-name">{t('itineraryBuilder.removedItem')}</span>
        )}
        <span className="it-item-meta">
          {attraction ? (
            <>
              {attraction.category}
              {attraction.avg_rating ? ` · ★ ${attraction.avg_rating.toFixed(1)}` : ''}
            </>
          ) : hotel ? (
            <>
              <span style={{ textTransform: 'capitalize' }}>{hotel.budget_tier}</span>
              {hotel.avg_rating ? ` · ★ ${hotel.avg_rating.toFixed(1)}` : ''}
            </>
          ) : null}
        </span>
      </div>
      <button
        type="button"
        className="it-item-remove"
        onClick={() => onRemove(item)}
        aria-label={`Remove ${attraction?.name || hotel?.name || 'item'} from this day`}
        title="Remove from day"
      >
        ✕
      </button>
    </div>
  )
}

/** Wraps a day's rows and FLIP-animates reorders: whenever a row's offset in
 * the list changes between renders, it is transformed back to its old spot
 * and released, so drag reordering glides instead of snapping. */
function DayItems({ children, dragActive }) {
  const ref = useRef(null)
  const positions = useRef(new Map())

  useLayoutEffect(() => {
    const container = ref.current
    if (!container) return
    const containerTop = container.getBoundingClientRect().top
    const prev = positions.current
    const next = new Map()
    for (const el of container.children) {
      const id = el.dataset.flipId
      if (!id) continue
      const top = el.getBoundingClientRect().top - containerTop
      next.set(id, top)
      const old = prev.get(id)
      const dy = old === undefined ? 0 : old - top
      if (dy) {
        el.style.transition = 'none'
        el.style.transform = `translateY(${dy}px)`
        requestAnimationFrame(() => {
          el.style.transition = 'transform 200ms var(--ease)'
          el.style.transform = ''
        })
      }
    }
    positions.current = next
  })

  return (
    <div ref={ref} className={`it-day-items${dragActive ? ' is-drag-active' : ''}`}>
      {children}
    </div>
  )
}

function formatDistance(meters) {
  if (typeof meters !== 'number') return ''
  if (meters < 1000) return `${Math.round(meters)} m`
  const km = meters / 1000
  return `${km >= 100 ? Math.round(km) : km.toFixed(1)} km`
}

function formatDuration(seconds) {
  if (typeof seconds !== 'number') return ''
  const mins = Math.round(seconds / 60)
  if (mins < 60) return `${mins} min`
  const h = Math.floor(mins / 60)
  const m = mins % 60
  return m ? `${h} h ${m} min` : `${h} h`
}

/** Per-day driving route summary + the optimize-order suggestion flow.
 * Hidden entirely until a day has two located stops (no route to show). */
function DayRouteSummary({ locatedItems, route, suggestion, onOptimize, onApply, onDismiss }) {
  const { t } = useTranslation()
  if (locatedItems.length < 2) return null

  // A suggestion is only shown while the day's order still matches the one it
  // was computed for — any reorder/add/remove silently retires it.
  const signature = locatedItems.map((i) => i.id).join(',')
  const live = suggestion && suggestion.signature === signature ? suggestion : null

  // First/last stops stay fixed, so with < 4 stops there is nothing to reorder.
  const canOptimize = locatedItems.length >= 4 && route?.state === 'ok'
  const applying = live?.state === 'applying'
  const savedSeconds =
    live?.route && route?.state === 'ok'
      ? route.total_duration_s - live.route.total_duration_s
      : 0
  const nameById = new Map(
    locatedItems.map((i) => [i.id, i.attraction?.name || 'Attraction'])
  )

  return (
    <div className="it-day-route-wrap">
      <div className="it-day-route">
        <span className="it-route-car" aria-hidden="true">🚗</span>
        {!route || route.state === 'loading' ? (
          <span className="it-route-text muted">{t('itineraryBuilder.calculatingRoute')}</span>
        ) : route.state === 'ok' ? (
          <span className="it-route-text">
            <strong>{formatDuration(route.total_duration_s)}</strong>
            {' · '}
            {formatDistance(route.total_distance_m)} {t('itineraryBuilder.drivingBetween')}{' '}
            {locatedItems.length} {t('itineraryBuilder.stops')}
          </span>
        ) : (
          <span className="it-route-text muted">{t('itineraryBuilder.routeUnavailable')}</span>
        )}
        {canOptimize && (
          <button
            type="button"
            className="it-route-optimize"
            onClick={onOptimize}
            disabled={live?.state === 'loading' || applying}
          >
            {live?.state === 'loading' ? t('itineraryBuilder.optimizingBtn') : t('itineraryBuilder.optimizeBtn')}
          </button>
        )}
      </div>

      {live?.state === 'already-optimal' && (
        <p className="it-route-note ok" role="status">
          {t('itineraryBuilder.alreadyOptimal')}
        </p>
      )}
      {live?.state === 'error' && (
        <p className="it-route-note muted" role="status">
          {t('itineraryBuilder.suggestionError')}
        </p>
      )}
      {(live?.state === 'ready' || applying) && (
        <div className="it-route-suggest" role="status">
          <p className="it-route-suggest-title">
            {t('itineraryBuilder.fasterOrderFound')}
            {savedSeconds > 60 ? `${t('itineraryBuilder.savesAbout')} ${formatDuration(savedSeconds)}` : ''}
          </p>
          <ol className="it-route-suggest-list">
            {live.itemIds.map((itemId) => (
              <li key={itemId}>{nameById.get(itemId)}</li>
            ))}
          </ol>
          <div className="it-route-suggest-actions">
            <button
              type="button"
              className="btn btn-primary"
              onClick={onApply}
              disabled={applying}
            >
              {applying ? t('itineraryBuilder.applyingBtn') : t('itineraryBuilder.applyBtn')}
            </button>
            <button
              type="button"
              className="btn btn-ghost"
              onClick={onDismiss}
              disabled={applying}
            >
              {t('itineraryBuilder.dismissBtn')}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/** Coarse condition family, used only to tint the weather chip so days are
 *  scannable at a glance (sunny warm, rainy blue, cloudy neutral…). */
function weatherGroup(condition) {
  if (condition === 'Clear') return 'clear'
  if (condition === 'Clouds') return 'cloud'
  if (condition === 'Rain' || condition === 'Drizzle') return 'rain'
  if (condition === 'Thunderstorm') return 'storm'
  if (condition === 'Snow') return 'snow'
  if (['Mist', 'Fog', 'Haze', 'Smoke', 'Dust'].includes(condition)) return 'mist'
  return 'default'
}

/** Weather, as part of the day's at-a-glance line — a compact, tinted chip. */
function DayGlanceWeather({ weather }) {
  const { t } = useTranslation()
  if (!weather) return null
  if (weather.state === 'ok') {
    const label = weather.description || weather.condition || ''
    const title = [
      label,
      weather.placeName ? `at ${weather.placeName}` : null,
    ]
      .filter(Boolean)
      .join(' ')
    const showRain =
      typeof weather.rainChance === 'number' && weather.rainChance >= 20
    return (
      <span
        className={`it-weather-chip${weather.isBad ? ' is-bad' : ''}`}
        data-cond={weatherGroup(weather.condition)}
        title={title}
      >
        <span className="it-weather-chip-icon" aria-hidden="true">
          {weather.emoji}
        </span>
        <span className="it-weather-chip-temp">
          {typeof weather.temp === 'number' ? `${Math.round(weather.temp)}°` : '—'}
          {typeof weather.tempMin === 'number' && (
            <span className="it-weather-chip-lo">{Math.round(weather.tempMin)}°</span>
          )}
        </span>
        {showRain && (
          <span className="it-weather-chip-rain">
            <span aria-hidden="true">💧</span>
            {weather.rainChance}%
          </span>
        )}
        {weather.isCurrent && <span className="it-weather-chip-now">Now</span>}
      </span>
    )
  }
  if (weather.state === 'out-of-range') {
    return (
      <span
        className="it-weather-chip is-muted"
        title="Beyond the 5-day forecast window"
      >
        <span className="it-weather-chip-icon" aria-hidden="true">🗓️</span>
        <span className="it-weather-chip-note">{t('itineraryBuilder.forecastLater')}</span>
      </span>
    )
  }
  if (weather.state === 'unavailable') {
    return (
      <span className="it-weather-chip is-muted">
        <span className="it-weather-chip-icon" aria-hidden="true">🌡️</span>
        <span className="it-weather-chip-note">{t('itineraryBuilder.weatherNa')}</span>
      </span>
    )
  }
  return null
}

/** Loading skeleton shaped like the real page, so nothing jumps on arrival. */
function BuilderSkeleton() {
  return (
    <div className="page it-page" aria-busy="true" aria-label="Loading your trip">
      <div className="it-skel it-skel-hero" />
      <div className="it-skel-strip" aria-hidden="true">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="it-skel it-skel-chip" />
        ))}
      </div>
      <div className="it-layout">
        <div className="it-timeline">
          {[0, 1].map((d) => (
            <div key={d} className="it-skel-day card" aria-hidden="true">
              <div className="it-skel it-skel-title" />
              {[0, 1, 2].map((r) => (
                <div key={r} className="it-skel it-skel-row" />
              ))}
            </div>
          ))}
        </div>
        <aside className="it-summary" aria-hidden="true">
          <div className="it-skel it-skel-rail" />
        </aside>
      </div>
    </div>
  )
}

// import AITripViewer from './AITripViewer'

export default function ItineraryBuilder() {
  const { t } = useTranslation()
  const { id } = useParams()
  const location = useLocation()

  const [itinerary, setItinerary] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadError, setLoadError] = useState(false)

  // Editable meta, kept apart from the saved itinerary so typing is instant.
  const [titleDraft, setTitleDraft] = useState('')
  const [startDraft, setStartDraft] = useState('')
  const [endDraft, setEndDraft] = useState('')
  const [saveState, setSaveState] = useState('idle') // idle | saving | saved | error

  const [pickerDay, setPickerDay] = useState(null) // day number or null
  const [drag, setDrag] = useState(null) // { itemId, day }
  const dragChanged = useRef(false)
  const preDragItems = useRef(null)
  
  const [generatingPdf, setGeneratingPdf] = useState(false)
  const [pdfError, setPdfError] = useState(null)
  const pdfContainerRef = useRef(null)

  // Which day the day-strip highlights; on narrow viewports it's also the one
  // day shown (single-day-at-a-time mode — the rest hide via CSS).
  const [activeDay, setActiveDay] = useState(1)
  const dayRefs = useRef({})

  // Weather-aware suggestions: fetched on demand per day (keyed by day number).
  const [weatherState, setWeatherState] = useState('idle') // idle | loading | done | error
  const [dayWeather, setDayWeather] = useState({}) // { [day]: { state, ... } }

  // Per-day driving routes, refreshed as a day's stop order changes.
  const [dayRoutes, setDayRoutes] = useState({}) // { [day]: { state, total_*, legs } }
  const routeFetchedSig = useRef({}) // { [day]: "id,id,..." } — last order fetched
  const [routeSuggestion, setRouteSuggestion] = useState(null) // one open suggestion

  useEffect(() => {
    let cancelled = false
    setLoading(true)
    setLoadError(false)
    fetchItinerary(id)
      .then((data) => {
        if (cancelled) return
        setItinerary(data)
        setTitleDraft(data.title)
        setStartDraft(data.start_date || '')
        setEndDraft(data.end_date || '')
      })
      .catch(() => {
        if (!cancelled) setLoadError(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [id])

  const items = useMemo(() => itinerary?.items || [], [itinerary])

  const totalDays = useMemo(() => {
    const fromDates = dayCount(itinerary?.start_date, itinerary?.end_date)
    if (fromDates) return fromDates
    return Math.max(1, ...items.map((i) => i.day_number || 1))
  }, [itinerary, items])

  const daysCovered = useMemo(
    () => new Set(items.map((i) => i.day_number)).size,
    [items]
  )

  const plannedIds = useMemo(
    () => new Set(items.map((i) => i.attraction_id)),
    [items]
  )

  // IDs already in the day that the picker is open for — used to block same-day duplicates.
  const dayPlannedIds = useMemo(() => {
    if (pickerDay === null) return new Set()
    return new Set(
      items.filter((i) => i.day_number === pickerDay).map((i) => i.attraction_id)
    )
  }, [items, pickerDay])

  // The trip's cover: the first stop that has any photo (admin-uploaded
  // image_url first, then a bundled scene), falling back to a signature scene.
  const coverScene = useMemo(() => {
    for (const it of items) {
      if (!it.attraction) continue
      // Admin-uploaded image takes priority over bundled photos.
      if (it.attraction.image_url) {
        return { src: it.attraction.image_url, position: '50% 50%' }
      }
      const photo = attractionPhoto(it.attraction)
      if (photo) return photo
    }
    return scenes.sigiriyaAerial
  }, [items])

  const datesInvalid = Boolean(
    startDraft && endDraft && !dayCount(startDraft, endDraft)
  )

  // The trip may shrink (dates edited) — keep the highlighted day in range.
  useEffect(() => {
    if (activeDay > totalDays) setActiveDay(totalDays)
  }, [activeDay, totalDays])

  // "Saved ✓" is a moment, not a permanent banner — let it fade back out.
  useEffect(() => {
    if (saveState !== 'saved') return undefined
    const timer = setTimeout(() => setSaveState('idle'), 2500)
    return () => clearTimeout(timer)
  }, [saveState])

  // Scroll-spy: as the timeline scrolls under the sticky day strip, highlight
  // the day currently in view. (On mobile only the active day is visible, so
  // the observer simply never fires there.)
  useEffect(() => {
    if (loading || totalDays <= 1) return undefined
    const sections = Object.values(dayRefs.current).filter(Boolean)
    const observer = new IntersectionObserver(
      (entries) => {
        const visible = entries
          .filter((e) => e.isIntersecting)
          .sort((a, b) => a.boundingClientRect.top - b.boundingClientRect.top)
        if (visible[0]) setActiveDay(Number(visible[0].target.dataset.day))
      },
      { rootMargin: '-30% 0px -55% 0px' }
    )
    sections.forEach((s) => observer.observe(s))
    return () => observer.disconnect()
  }, [loading, totalDays])

  const goToDay = (day) => {
    const next = Math.min(Math.max(day, 1), totalDays)
    setActiveDay(next)
    // Wait a frame so a day hidden in mobile single-day mode is visible first.
    requestAnimationFrame(() => {
      dayRefs.current[next]?.scrollIntoView({ behavior: 'smooth', block: 'start' })
    })
  }

  // ---- Weather-aware suggestions ---------------------------------------------

  // First planned attraction per day drives that day's forecast. A change to any
  // day's opener (or the trip's start date) invalidates a previously run check.
  const firstStopSignature = useMemo(() => {
    const byDay = {}
    for (const it of items) {
      if (byDay[it.day_number] === undefined) byDay[it.day_number] = it.attraction_id
    }
    return `${itinerary?.start_date || ''}|${JSON.stringify(byDay)}`
  }, [items, itinerary])

  useEffect(() => {
    setWeatherState('idle')
    setDayWeather({})
  }, [firstStopSignature])

  const runWeatherCheck = async () => {
    setWeatherState('loading')
    const results = {}
    const byLocation = new Map() // "lat,lng" -> weather payload (or {error}) — fetch once
    const days = Array.from({ length: totalDays }, (_, i) => i + 1)

    try {
      for (const day of days) {
        const first = items.find((i) => i.day_number === day)?.attraction
        if (
          !first ||
          typeof first.latitude !== 'number' ||
          typeof first.longitude !== 'number'
        ) {
          results[day] = { state: 'no-location' }
          continue
        }

        const key = `${first.latitude.toFixed(2)},${first.longitude.toFixed(2)}`
        let weather = byLocation.get(key)
        if (!weather) {
          try {
            weather = await fetchWeather(first.latitude, first.longitude)
          } catch {
            weather = { error: true }
          }
          byLocation.set(key, weather)
        }

        if (weather.error || weather.available === false) {
          results[day] = { state: 'unavailable' }
          continue
        }

        // Line the day's calendar date up against a forecast day; when the trip
        // has no dates, fall back to current conditions as a general indicator.
        const iso = dayIsoDate(itinerary.start_date, day)
        let block = iso ? weather.forecast?.find((f) => f.date === iso) : null
        let isCurrent = false
        if (!block && !iso && weather.current) {
          block = weather.current
          isCurrent = true
        }
        if (!block) {
          results[day] = { state: 'out-of-range' }
          continue
        }

        results[day] = {
          state: 'ok',
          isBad: Boolean(block.is_bad),
          condition: block.condition,
          description: block.description,
          emoji: weatherEmoji(block.condition),
          temp: block.temp_max_c ?? block.temp_c ?? null,
          tempMin: block.temp_min_c ?? null,
          rainChance: block.rain_chance ?? null,
          isCurrent,
          placeName: first.name,
        }
      }
      setDayWeather(results)
      setWeatherState('done')
    } catch {
      setWeatherState('error')
    }
  }

  const okDays = Object.values(dayWeather).filter((w) => w.state === 'ok')
  const badDayCount = okDays.filter((w) => w.isBad).length
  const anyForecast = okDays.length > 0

  // ---- Per-day driving routes -------------------------------------------------

  // Only stops with coordinates can be routed; grouped per day in current order.
  const locatedByDay = useMemo(() => {
    const byDay = {}
    for (const it of items) {
      const a = it.attraction
      if (typeof a?.latitude === 'number' && typeof a?.longitude === 'number') {
        ;(byDay[it.day_number] ||= []).push(it)
      }
    }
    return byDay
  }, [items])

  const routeSignature = useMemo(
    () =>
      Object.entries(locatedByDay)
        .map(([day, list]) => `${day}:${list.map((i) => i.id).join(',')}`)
        .join('|'),
    [locatedByDay]
  )

  // Fresh trip → forget everything fetched for the previous one.
  useEffect(() => {
    routeFetchedSig.current = {}
    setDayRoutes({})
    setRouteSuggestion(null)
    setActiveDay(1)
  }, [id])

  // Fetch/refresh each routable day's route whenever its stop order changes.
  // Debounced, and paused mid-drag so we only ask once the drop settles; the
  // backend caches per ordered stop list, so re-asking is cheap anyway.
  useEffect(() => {
    if (drag || !itinerary) return undefined
    const timer = setTimeout(() => {
      // Days that lost their route (now < 2 located stops) fall back to hidden.
      for (const day of Object.keys(routeFetchedSig.current)) {
        if ((locatedByDay[day] || []).length < 2) {
          delete routeFetchedSig.current[day]
          setDayRoutes((prev) => {
            const next = { ...prev }
            delete next[day]
            return next
          })
        }
      }
      for (const [day, list] of Object.entries(locatedByDay)) {
        if (list.length < 2) continue
        const sig = list.map((i) => i.id).join(',')
        if (routeFetchedSig.current[day] === sig) continue
        routeFetchedSig.current[day] = sig
        setDayRoutes((prev) => ({ ...prev, [day]: { state: 'loading' } }))
        fetchDayRoute(itinerary.id, day)
          .then((data) => {
            if (routeFetchedSig.current[day] !== sig) return // superseded
            setDayRoutes((prev) => ({
              ...prev,
              [day]: { state: 'ok', ...data.route },
            }))
          })
          .catch(() => {
            if (routeFetchedSig.current[day] !== sig) return
            setDayRoutes((prev) => ({ ...prev, [day]: { state: 'unavailable' } }))
          })
      }
    }, 500)
    return () => clearTimeout(timer)
  }, [routeSignature, drag, itinerary, locatedByDay])

  // Trip-wide driving total for the summary rail (days with a live route only).
  const totalDriveSeconds = useMemo(
    () =>
      Object.values(dayRoutes)
        .filter((r) => r.state === 'ok')
        .reduce((sum, r) => sum + (r.total_duration_s || 0), 0),
    [dayRoutes]
  )

  const handleOptimize = async (day) => {
    const list = locatedByDay[day] || []
    const signature = list.map((i) => i.id).join(',')
    setRouteSuggestion({ day, state: 'loading', signature })
    try {
      const data = await fetchDayRoute(itinerary.id, day, { optimize: true })
      const suggested = data.suggested_item_order || []
      if (suggested.join(',') === signature) {
        setRouteSuggestion({ day, state: 'already-optimal', signature })
      } else {
        setRouteSuggestion({
          day,
          state: 'ready',
          signature,
          itemIds: suggested,
          route: data.route,
        })
      }
    } catch {
      setRouteSuggestion({ day, state: 'error', signature })
    }
  }

  const applyRouteSuggestion = async () => {
    if (!routeSuggestion?.itemIds) return
    const { day, itemIds } = routeSuggestion
    // The reorder endpoint wants the day's complete order — stops without
    // coordinates weren't routed, so they keep their place at the end.
    const unlocated = items
      .filter((i) => i.day_number === day && !itemIds.includes(i.id))
      .map((i) => i.id)
    setRouteSuggestion({ ...routeSuggestion, state: 'applying' })
    setSaveState('saving')
    try {
      const updated = await reorderItineraryItems(itinerary.id, day, [
        ...itemIds,
        ...unlocated,
      ])
      setItinerary(updated)
      setRouteSuggestion(null)
      setSaveState('saved')
    } catch {
      setRouteSuggestion({ ...routeSuggestion, state: 'error' })
      setSaveState('error')
    }
  }

  // ---- Meta editing (title + dates), saved on commit ------------------------

  const saveMeta = async (fields) => {
    setSaveState('saving')
    try {
      const updated = await updateItinerary(itinerary.id, fields)
      // The server may pull stranded items onto the last day when a trip
      // shrinks — adopt its state wholesale so the timeline matches.
      setItinerary(updated)
      setSaveState('saved')
    } catch {
      setSaveState('error')
    }
  }

  const commitTitle = () => {
    const next = titleDraft.trim()
    if (!next) {
      setTitleDraft(itinerary.title) // don't allow blanking the title
      return
    }
    if (next !== itinerary.title) saveMeta({ title: next })
  }

  const commitDates = (nextStart, nextEnd) => {
    setStartDraft(nextStart)
    setEndDraft(nextEnd)
    if (nextStart && nextEnd && !dayCount(nextStart, nextEnd)) return // invalid — hold
    saveMeta({ start_date: nextStart || null, end_date: nextEnd || null })
  }

  // ---- Items: add / remove / reorder / AI generate ---------------------------

  const handleAutoGenerate = async (prefsOverride = null) => {
    setSaveState('saving')
    try {
      const generatedItems = await generateItineraryWithAI({
        startDate: itinerary.start_date,
        endDate: itinerary.end_date,
        preferences: { 
          description: itinerary.description,
          start_location: itinerary.start_location,
          end_location: itinerary.end_location,
          stops: itinerary.stops,
          trip_type: itinerary.trip_type,
          user_preferences: prefsOverride || location.state?.initialPreferences
        } 
      })
      
      // Save items to backend one by one
      let updatedItems = [...itinerary.items]
      for (const genItem of generatedItems) {
        const item = await addItineraryItem(itinerary.id, {
          attractionId: genItem.attraction_id,
          hotelId: genItem.hotel_id,
          dayNumber: genItem.day_number,
        })
        updatedItems.push(item)
      }
      
      setItinerary((prev) => ({ ...prev, items: updatedItems }))
      setSaveState('saved')
    } catch (err) {
      console.error(err)
      setSaveState('error')
    }
  }

  const handleAdd = async (attraction) => {
    // Block same-day duplicates — the same attraction cannot be added twice to
    // the same day. A toast-like guard here prevents the API call entirely.
    const alreadyInDay = items.some(
      (i) => i.day_number === pickerDay && i.attraction_id === attraction.id
    )
    if (alreadyInDay) {
      // Throw so the picker surfaces the "already added" state instead of ✓ Added.
      throw new Error('duplicate')
    }
    try {
      const item = await addItineraryItem(itinerary.id, {
        attractionId: attraction.id,
        dayNumber: pickerDay,
      })
      setItinerary((prev) => ({ ...prev, items: [...prev.items, item] }))
    } catch (err) {
      setSaveState('error')
      throw err // let the picker skip its "Added ✓" flash
    }
  }

  const handleRemove = async (item) => {
    const previous = itinerary.items
    setItinerary((prev) => ({
      ...prev,
      items: prev.items.filter((i) => i.id !== item.id),
    }))
    try {
      await removeItineraryItem(itinerary.id, item.id)
    } catch {
      setItinerary((prev) => ({ ...prev, items: previous })) // removal failed
      setSaveState('error')
    }
  }

  const handleDragStart = (item) => {
    setDrag({ itemId: item.id, day: item.day_number })
    dragChanged.current = false
    preDragItems.current = itinerary.items
  }

  // Reorder locally as the dragged row passes over a sibling in the same day.
  const handleDragEnter = (target) => {
    if (!drag || target.id === drag.itemId || target.day_number !== drag.day) return
    setItinerary((prev) => {
      const list = [...prev.items]
      const from = list.findIndex((i) => i.id === drag.itemId)
      const to = list.findIndex((i) => i.id === target.id)
      if (from === -1 || to === -1) return prev
      const [moved] = list.splice(from, 1)
      list.splice(to, 0, moved)
      dragChanged.current = true
      return { ...prev, items: list }
    })
  }

  const handleDragEnd = async () => {
    const current = drag
    setDrag(null)
    if (!current || !dragChanged.current) return
    const dayIds = itinerary.items
      .filter((i) => i.day_number === current.day)
      .map((i) => i.id)
    setSaveState('saving')
    try {
      const updated = await reorderItineraryItems(itinerary.id, current.day, dayIds)
      setItinerary(updated)
      setSaveState('saved')
    } catch {
      // Persisting the new order failed — snap back to the pre-drag order.
      setItinerary((prev) => ({ ...prev, items: preDragItems.current }))
      setSaveState('error')
    }
  }

  useEffect(() => {
    // Auto-generate if it's a new AI itinerary
    if (itinerary?.is_ai_generated && itinerary?.items?.length === 0 && location.state?.initialPreferences) {
      handleAutoGenerate(location.state.initialPreferences)
    }
  }, [itinerary?.is_ai_generated])

  const handleGeneratePdf = async () => {
    setGeneratingPdf(true)
    setPdfError(null)
    try {
       const { default: api } = await import('../services/api')
       const response = await api.post('/ai/generate-pdf-summary', { itinerary_id: itinerary.id })
       
       if (pdfContainerRef.current) {
          const { marked } = await import('marked')
          
          const tempDiv = document.createElement('div')
          tempDiv.className = 'modern-pdf-container'
          
          const startDate = itinerary.start_date ? new Date(itinerary.start_date).toLocaleDateString() : 'TBD'
          const endDate = itinerary.end_date ? new Date(itinerary.end_date).toLocaleDateString() : 'TBD'
          
          const parsedContent = await marked.parse(response.data.markdown)
          
          tempDiv.innerHTML = `
            <div class="pdf-header">
              <h1>${itinerary.title}</h1>
              <p>${startDate} - ${endDate}</p>
            </div>
            <div class="pdf-content">${parsedContent}</div>
          `
          
          pdfContainerRef.current.appendChild(tempDiv)
          
          const html2pdf = (await import('html2pdf.js')).default
          const opt = {
            margin: [0, 0, 10, 0], // Top margin 0 for full-width banner
            filename: `${itinerary.title.replace(/\s+/g, '_')}_Plan.pdf`,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2 },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
          }
          await html2pdf().from(tempDiv).set(opt).save()
          
          pdfContainerRef.current.innerHTML = ''
          setGeneratingPdf(false)
       }
    } catch (err) {
       console.error(err)
       setPdfError('Failed to generate PDF')
       setGeneratingPdf(false)
    }
  }

  // ---- Render ------------------------------------------------------------------

  if (loading) return <BuilderSkeleton />

  if (loadError || !itinerary) {
    return (
      <div className="page page-narrow">
        <div className="explore-empty card">
          <span className="explore-empty-icon" aria-hidden="true">🧳</span>
          <h3>{t('itineraryBuilder.tripNotFound')}</h3>
          <p>{t('itineraryBuilder.tripNotExist')}</p>
          <Link to="/itineraries" className="btn btn-primary">
            {t('itineraryBuilder.backToMyItineraries')}
          </Link>
        </div>
      </div>
    )
  }

  const range = formatTripRange(itinerary.start_date, itinerary.end_date)
  const dayNumbers = Array.from({ length: totalDays }, (_, i) => i + 1)

  return (
    <div className="page it-page">
      <div style={{ display: 'none' }} ref={pdfContainerRef} />
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Link to="/itineraries" className="detail-back">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M19 12H5m0 0 6-6m-6 6 6 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
          {t('itineraryBuilder.myItineraries')}
        </Link>
        <button className="btn btn-primary" onClick={handleGeneratePdf} disabled={generatingPdf}>
          {generatingPdf ? t('itineraryBuilder.generatingPdf') : t('itineraryBuilder.downloadPdf')}
        </button>
      </div>

      {/* Trip cover: photo hero with the editable title, then a slim bar for
          dates + save status so form controls stay off the photograph. */}
      <header className="it-hero card">
        <div className="it-hero-media">
          <img
            src={coverScene.src}
            style={{ objectPosition: coverScene.position }}
            alt=""
            aria-hidden="true"
          />
          <div className="it-hero-scrim" aria-hidden="true" />
          <div className="it-hero-content">
            <input
              className="it-hero-title"
              value={titleDraft}
              onChange={(e) => setTitleDraft(e.target.value)}
              onBlur={commitTitle}
              onKeyDown={(e) => e.key === 'Enter' && e.currentTarget.blur()}
              maxLength={200}
              aria-label={t('itineraryBuilder.tripNameAria')}
            />
            <p className="it-hero-facts">
              {totalDays} {totalDays === 1 ? t('itineraries.dayCount') : t('itineraries.daysCount')}
              {items.length > 0 &&
                ` · ${items.length} ${items.length === 1 ? t('itineraries.placeCount') : t('itineraries.placesCount')}`}
              {range && ` · ${range}`}
            </p>
          </div>
        </div>
        <div className="it-hero-bar">
          <div className="it-hero-date">
            <label className="it-hero-date-label" htmlFor="it-start">{t('itineraryBuilder.startLabel')}</label>
            <input
              id="it-start"
              className="input it-hero-date-input"
              type="date"
              value={startDraft}
              onChange={(e) => commitDates(e.target.value, endDraft)}
            />
          </div>
          <span className="it-hero-date-arrow" aria-hidden="true">→</span>
          <div className="it-hero-date">
            <label className="it-hero-date-label" htmlFor="it-end">{t('itineraryBuilder.endLabel')}</label>
            <input
              id="it-end"
              className="input it-hero-date-input"
              type="date"
              value={endDraft}
              min={startDraft || undefined}
              onChange={(e) => commitDates(startDraft, e.target.value)}
            />
          </div>
          {datesInvalid && (
            <p className="it-days-hint it-days-hint-error">
              {t('itineraryBuilder.endDateBeforeStart')}
            </p>
          )}
          <span
            className={`it-save-chip it-save-${saveState}`}
            role="status"
            aria-live="polite"
          >
            {saveState === 'saving' && t('itineraryBuilder.saving')}
            {saveState === 'saved' && t('itineraryBuilder.saved')}
            {saveState === 'error' && t('itineraryBuilder.saveError')}
          </span>
        </div>
      </header>

      {/* Day strip: the trip's shape at a glance — one chip per day with stop
          density and (once checked) weather. Click to jump; on mobile it also
          switches which single day is shown. */}
      {totalDays > 1 && (
        <nav className="it-daystrip" aria-label="Trip days">
          {dayNumbers.map((day) => {
            const count = items.filter((i) => i.day_number === day).length
            const stripDate = dayDateLabel(itinerary.start_date, day)
            const w = dayWeather[day]
            return (
              <button
                key={day}
                type="button"
                className={`it-strip-chip${activeDay === day ? ' is-active' : ''}`}
                onClick={() => goToDay(day)}
                aria-current={activeDay === day ? 'true' : undefined}
              >
                <span className="it-strip-top">
                  {t('itineraryBuilder.dayNum')} {day}
                  {w?.state === 'ok' && (
                    <span className="it-strip-emoji" aria-hidden="true">{w.emoji}</span>
                  )}
                </span>
                <span className="it-strip-sub">
                  {stripDate || (count ? `${count} ${t('itineraryBuilder.stops')}` : t('itineraryBuilder.free'))}
                </span>
                <span
                  className="it-strip-dots"
                  aria-label={`${count} stop${count === 1 ? '' : 's'} planned`}
                >
                  {count === 0 ? (
                    <span className="it-strip-dot is-empty" />
                  ) : (
                    Array.from({ length: Math.min(count, 6) }, (_, i) => (
                      <span key={i} className="it-strip-dot" />
                    ))
                  )}
                </span>
              </button>
            )
          })}
        </nav>
      )}

      <div className="it-layout">
        <div className="it-timeline">
          {items.length === 0 && (
            <div className="it-invite card">
              <div className="it-invite-photos" aria-hidden="true">
              {[scenes.sigiriyaGround, scenes.nineArch, scenes.coconutTreeHill].map(
                (scene) => (
                  <img
                    key={scene.src}
                    src={scene.src}
                    style={{ objectPosition: scene.position }}
                    alt=""
                  />
                )
              )}
              </div>
              <h3>{t('itineraryBuilder.startBuilding')}</h3>
              <p>
                {t('itineraryBuilder.startBuildingDesc')}
              </p>
              <div style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap', justifyContent: 'center' }}>
                <button
                  type="button"
                  className="btn btn-primary"
                  onClick={() => setPickerDay(1)}
                >
                  {t('itineraryBuilder.addFirstPlaceBtn')}
                </button>
                <button
                  type="button"
                  className="btn btn-secondary"
                  onClick={() => handleAutoGenerate()}
                  disabled={saveState === 'saving'}
                >
                  {saveState === 'saving' ? t('itineraryBuilder.generatingBtn') : t('itineraryBuilder.autoGenerateBtn')}
                </button>
              </div>
            </div>
          )}

          {dayNumbers.map((day) => {
            const dayItems = items.filter((i) => i.day_number === day)
            const dateLabel = dayDateLabel(itinerary.start_date, day)
            const dayW = dayWeather[day]
            return (
              <section
                key={day}
                className={`it-day${activeDay === day ? ' is-active' : ''}`}
                aria-label={`Day ${day}`}
                data-day={day}
                ref={(el) => {
                  dayRefs.current[day] = el
                }}
              >
                <div className="it-day-rail" aria-hidden="true">
                  <span className="it-day-dot">{day}</span>
                  <span className="it-day-line" />
                </div>
                <div className="it-day-main">
                  <div className="it-day-head">
                    <div className="it-day-heading">
                      <h2 className="it-day-title">{t('itineraryBuilder.dayNum')} {day}</h2>
                      {dateLabel && <span className="it-day-date">{dateLabel}</span>}
                    </div>
                    <div className="it-day-glance">
                      <DayGlanceWeather weather={dayW} />
                      <span className="it-glance-count">
                        {dayItems.length
                          ? `${dayItems.length} ${t('itineraryBuilder.stops')}`
                          : t('itineraryBuilder.freeDay')}
                      </span>
                    </div>
                  </div>

                  {dayW?.state === 'ok' && dayW.isBad && (
                    <div className="it-day-warn" role="status">
                      <span className="it-day-warn-icon" aria-hidden="true">☔</span>
                      <span>
                        <strong>
                          {dayW.description
                            ? dayW.description.charAt(0).toUpperCase() +
                              dayW.description.slice(1)
                            : t('itineraryBuilder.rainExpected')}
                          {typeof dayW.rainChance === 'number'
                            ? ` (${dayW.rainChance}%)`
                            : ''}
                          .
                        </strong>{' '}
                        {t('itineraryBuilder.indoorStopsSuggest')}
                      </span>
                    </div>
                  )}

                  {dayItems.length === 0 ? (
                    <button
                      type="button"
                      className="it-day-empty"
                      onClick={() => setPickerDay(day)}
                    >
                      <span className="it-day-empty-plus" aria-hidden="true">+</span>
                      {t('itineraryBuilder.nothingPlanned')}
                    </button>
                  ) : (
                    <>
                      <DayItems dragActive={drag?.day === day}>
                        {dayItems.map((item) => (
                          <DayItemRow
                            key={item.id}
                            item={item}
                            dragging={drag?.itemId === item.id}
                            onDragStart={handleDragStart}
                            onDragEnter={handleDragEnter}
                            onDragEnd={handleDragEnd}
                            onRemove={handleRemove}
                          />
                        ))}
                      </DayItems>

                      <DayRouteSummary
                        locatedItems={locatedByDay[day] || []}
                        route={dayRoutes[day]}
                        suggestion={routeSuggestion?.day === day ? routeSuggestion : null}
                        onOptimize={() => handleOptimize(day)}
                        onApply={applyRouteSuggestion}
                        onDismiss={() => setRouteSuggestion(null)}
                      />

                      <button
                        type="button"
                        className="btn btn-ghost it-day-add"
                        onClick={() => setPickerDay(day)}
                      >
                        {t('itineraryBuilder.addPlaceBtn')}
                      </button>
                    </>
                  )}
                </div>
              </section>
            )
          })}

          {/* Mobile-only: previous/next day, since narrow viewports show one
              day at a time. */}
          {totalDays > 1 && (
            <div className="it-day-nav">
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => goToDay(activeDay - 1)}
                disabled={activeDay <= 1}
              >
                ‹ {activeDay > 1 ? `${t('itineraryBuilder.dayNum')} ${activeDay - 1}` : t('itineraryBuilder.dayNum')}
              </button>
              <span className="it-day-nav-label">
                {t('itineraryBuilder.dayOfTotal', { activeDay, totalDays })}
              </span>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => goToDay(activeDay + 1)}
                disabled={activeDay >= totalDays}
              >
                {activeDay < totalDays ? `${t('itineraryBuilder.dayNum')} ${activeDay + 1}` : t('itineraryBuilder.dayNum')} ›
              </button>
            </div>
          )}
        </div>

        <aside className="it-summary">
          <div className="card card-pad">
            <h3 className="it-summary-title">{t('itineraryBuilder.tripSummary')}</h3>
            <dl className="it-summary-stats">
              <div className="it-summary-stat">
                <dt>{t('itineraryBuilder.daysStat')}</dt>
                <dd>{totalDays}</dd>
              </div>
              <div className="it-summary-stat">
                <dt>{t('itineraryBuilder.attractionsStat')}</dt>
                <dd>{items.length}</dd>
              </div>
              <div className="it-summary-stat">
                <dt>{t('itineraryBuilder.daysWithPlansStat')}</dt>
                <dd>
                  {daysCovered}/{totalDays}
                </dd>
              </div>
              {totalDriveSeconds > 0 && (
                <div className="it-summary-stat">
                  <dt>{t('itineraryBuilder.drivingStat')}</dt>
                  <dd className="it-summary-drive">{formatDuration(totalDriveSeconds)}</dd>
                </div>
              )}
            </dl>

            <div className="it-weather">
              <button
                type="button"
                className="btn btn-secondary btn-block it-weather-btn"
                onClick={runWeatherCheck}
                disabled={weatherState === 'loading'}
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
                  <circle cx="9" cy="9" r="3.5" stroke="currentColor" strokeWidth="1.7" />
                  <path
                    d="M9 2.5v1.6M9 13.9v1.6M2.5 9h1.6m9.8 0h1.6M4.4 4.4l1.1 1.1m7-1.1-1.1 1.1"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                  />
                  <path
                    d="M13 20.5h5.5a3 3 0 0 0 .4-5.97 4.2 4.2 0 0 0-8.2-.83A2.9 2.9 0 0 0 13 20.5Z"
                    stroke="currentColor"
                    strokeWidth="1.7"
                    strokeLinejoin="round"
                  />
                </svg>
                {weatherState === 'loading'
                  ? t('itineraryBuilder.checkingForecast')
                  : weatherState === 'done'
                    ? t('itineraryBuilder.refreshForecast')
                    : t('itineraryBuilder.getWeatherSuggestions')}
              </button>

              {weatherState === 'done' && (
                <p
                  className={`it-weather-summary ${
                    badDayCount ? 'warn' : anyForecast ? 'ok' : ''
                  }`}
                  role="status"
                >
                  {badDayCount
                    ? `⚠ Rain or storms forecast on ${badDayCount} day${
                        badDayCount > 1 ? 's' : ''
                      } — flagged in your timeline. Consider indoor stops there.`
                    : anyForecast
                      ? '☀ Clear conditions across your planned days.'
                      : 'Add a place with a location to a day to see its forecast.'}
                </p>
              )}

              {weatherState === 'error' && (
                <p className="it-weather-summary warn" role="status">
                  Couldn’t load the forecast right now. Please try again.
                </p>
              )}
            </div>
          </div>

          <TripMapCard items={items} totalDays={totalDays} routes={dayRoutes} startLocation={itinerary?.start_location} />
        </aside>
      </div>

      {pickerDay !== null && (
      <AttractionPicker
          dayNumber={pickerDay}
          dateLabel={dayDateLabel(itinerary.start_date, pickerDay)}
          plannedIds={plannedIds}
          alreadyInDayIds={dayPlannedIds}
          onAdd={handleAdd}
          onClose={() => setPickerDay(null)}
        />
      )}
    </div>
  )
}
