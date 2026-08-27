// Day-route map for the itinerary builder's summary rail. Pick a day and see
// its stops on an embedded Google Map, with the day's travel times spelled out:
//   • Two or more stops  → the driving route through them in planned order
//     (Maps Embed API directions mode), plus per-leg drive times woven into the
//     numbered stop list and a day total, sourced from the backend route.
//   • A single stop       → offer to route from "where I am now": once the user
//     shares their location, the map switches to a from-you driving route that
//     shows the travel time on the map itself. Until then it just pins the place.
// An "open in Google Maps" link carries the same route. Degrades to a link-only
// card when no API key is configured, and to a hint when the day has no located
// stops yet.

import { Fragment, useMemo, useState } from 'react'
import { useTranslation } from 'react-i18next'

const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

function coord(point) {
  if (typeof point === 'string') return point
  return `${point.latitude},${point.longitude}`
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

function embedSrc(stops, origin) {
  if (stops.length === 1 && !origin) {
    const stop = stops[0]
    const query = typeof stop === 'string' 
      ? stop 
      : `${stop.name}${stop.location ? `, ${stop.location}` : ''}`
    return (
      `https://www.google.com/maps/embed/v1/place?key=${MAPS_KEY}` +
      `&q=${encodeURIComponent(query)}&zoom=13`
    )
  }
  const points = origin ? [origin, ...stops] : stops
  const from = coord(points[0])
  const destination = coord(points[points.length - 1])
  const waypoints = points.slice(1, -1).map(coord).join('|')
  return (
    `https://www.google.com/maps/embed/v1/directions?key=${MAPS_KEY}` +
    `&origin=${encodeURIComponent(from)}` +
    `&destination=${encodeURIComponent(destination)}` +
    (waypoints ? `&waypoints=${encodeURIComponent(waypoints)}` : '') +
    `&mode=driving`
  )
}

function externalUrl(stops, origin) {
  if (stops.length === 1 && !origin) {
    const stop = stops[0]
    const query = typeof stop === 'string' 
      ? stop 
      : `${stop.name}${stop.location ? `, ${stop.location}` : ''}`
    return `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(query)}`
  }
  const points = origin ? [origin, ...stops] : stops
  const from = coord(points[0])
  const destination = coord(points[points.length - 1])
  const waypoints = points.slice(1, -1).map(coord).join('|')
  return (
    `https://www.google.com/maps/dir/?api=1&origin=${encodeURIComponent(from)}` +
    `&destination=${encodeURIComponent(destination)}` +
    (waypoints ? `&waypoints=${encodeURIComponent(waypoints)}` : '')
  )
}

export default function TripMapCard({ items, totalDays, routes, startLocation }) {
  const { t } = useTranslation()
  const [selectedDay, setSelectedDay] = useState(1)
  const day = Math.min(selectedDay, totalDays) // trip may have shrunk

  // The user's current position, shared on demand for single-stop routing.
  // It's day-independent, so it survives switching days once granted.
  const [myLocation, setMyLocation] = useState(null)
  const [geoState, setGeoState] = useState('idle') // idle | locating | denied | unsupported

  const requestLocation = () => {
    if (!navigator.geolocation) {
      setGeoState('unsupported')
      return
    }
    setGeoState('locating')
    navigator.geolocation.getCurrentPosition(
      (pos) => {
        setMyLocation({
          latitude: pos.coords.latitude,
          longitude: pos.coords.longitude,
        })
        setGeoState('ready')
      },
      () => setGeoState('denied'),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 300000 }
    )
  }

  // The day's stops that actually have coordinates, in planned order.
  const stops = useMemo(
    () => {
      const validItems = items.filter(
        (i) =>
          (i.attraction &&
            typeof i.attraction.latitude === 'number' &&
            typeof i.attraction.longitude === 'number') ||
          (i.hotel &&
            typeof i.hotel.latitude === 'number' &&
            typeof i.hotel.longitude === 'number')
      );
      
      const dayItems = validItems.filter((i) => i.day_number === day);
      if (dayItems.length === 0) return [];
      
      const finalStops = dayItems.map(i => i.attraction || i.hotel);
      
      if (day === 1 && startLocation) {
        finalStops.unshift(startLocation);
      } else if (day > 1) {
        const prevItems = validItems.filter((i) => i.day_number < day);
        if (prevItems.length > 0) {
          const prevLast = prevItems[prevItems.length - 1]
          finalStops.unshift(prevLast.attraction || prevLast.hotel);
        }
      }
      
      if (day === totalDays && totalDays > 1) {
        if (startLocation) {
          finalStops.push(startLocation);
        } else {
          const firstOverall = validItems[0].attraction || validItems[0].hotel;
          if (finalStops[finalStops.length - 1]?.id !== firstOverall.id) {
            finalStops.push(firstOverall);
          }
        }
      }
      
      return finalStops;
    },
    [items, day, totalDays, startLocation]
  )

  const dayNumbers = Array.from({ length: totalDays }, (_, i) => i + 1)

  // Backend driving route for this day (2+ stops only) → per-leg + total times.
  // legs[i] is the drive from stops[i] to stops[i+1], so they align by index.
  const route = routes?.[day]
  const legs = route?.state === 'ok' ? route.legs || [] : []

  // A single stop is only routed from the user's location once it's shared.
  const singleWithLocation = stops.length === 1 && myLocation
  const origin = singleWithLocation ? myLocation : null

  return (
    <div className="card card-pad it-map-card">
      <h3 className="it-summary-title">{t('itineraryBuilder.map.dayMap')}</h3>

      {totalDays > 1 && (
        <div className="it-map-days" role="tablist" aria-label={t('itineraryBuilder.map.pickDay')}>
          {dayNumbers.map((d) => (
            <button
              key={d}
              type="button"
              role="tab"
              aria-selected={d === day}
              className={`it-map-day-btn${d === day ? ' active' : ''}`}
              onClick={() => setSelectedDay(d)}
            >
              {d}
            </button>
          ))}
        </div>
      )}

      {stops.length === 0 ? (
        <p className="it-map-empty">
          {t('itineraryBuilder.map.emptyMap', { day })}
        </p>
      ) : (
        <>
          {MAPS_KEY ? (
            <div className="it-map-frame">
              <iframe
                title={`Map of day ${day} stops`}
                src={embedSrc(stops, origin)}
                loading="lazy"
                referrerPolicy="no-referrer-when-downgrade"
                allowFullScreen
              />
            </div>
          ) : (
            <p className="it-map-empty">
              {t('itineraryBuilder.map.notConfigured')}
            </p>
          )}

          {/* Single stop: route from the user's own location on request, so the
              map shows how far it is and how long it takes to get there. */}
          {stops.length === 1 &&
            (singleWithLocation ? (
              <p className="it-map-total">
                <span aria-hidden="true">🧭</span>
                {t('itineraryBuilder.map.routeShown')}
              </p>
            ) : (
              <div className="it-map-fromme">
                <button
                  type="button"
                  className="btn btn-secondary btn-block"
                  onClick={requestLocation}
                  disabled={geoState === 'locating'}
                >
                  {geoState === 'locating'
                    ? t('itineraryBuilder.map.findingYou')
                    : t('itineraryBuilder.map.showRoute')}
                </button>
                {geoState === 'denied' && (
                  <p className="it-map-geo-note">
                    {t('itineraryBuilder.map.geoDenied')}
                  </p>
                )}
                {geoState === 'unsupported' && (
                  <p className="it-map-geo-note">
                    {t('itineraryBuilder.map.geoUnsupported')}
                  </p>
                )}
              </div>
            ))}

          {/* Multi-stop day total, from the backend driving route. */}
          {route?.state === 'ok' && stops.length > 1 && (
            <p className="it-map-total">
              <span aria-hidden="true">🚗</span>
              <strong>{formatDuration(route.total_duration_s)}</strong>
              {' · '}
              {formatDistance(route.total_distance_m)} {t('itineraryBuilder.map.drivingStops', { stops: stops.length })}
            </p>
          )}
          {route?.state === 'loading' && stops.length > 1 && (
            <p className="it-map-total muted">{t('itineraryBuilder.map.calculatingDrive')}</p>
          )}

          <ol className="it-map-stops">
            {stops.map((stop, index) => (
              <Fragment key={`${typeof stop === 'string' ? stop : stop.id}-${index}`}>
                <li className="it-map-stop">
                  <span className="it-map-stop-num" aria-hidden="true">
                    {index + 1}
                  </span>
                  <span className="it-map-stop-name">
                    {typeof stop === 'string' ? t('itineraryBuilder.map.start', { stop }) : stop.name}
                  </span>
                </li>
                {legs[index] && (
                  <li className="it-map-leg" aria-hidden="true">
                    <span className="it-map-leg-line" />
                    <span className="it-map-leg-text">
                      {formatDuration(legs[index].duration_s)}
                      {' · '}
                      {formatDistance(legs[index].distance_m)}
                    </span>
                  </li>
                )}
              </Fragment>
            ))}
          </ol>

          <a
            className="it-map-link"
            href={externalUrl(stops, origin)}
            target="_blank"
            rel="noreferrer"
          >
            {stops.length > 1 || singleWithLocation
              ? t('itineraryBuilder.map.openRoute')
              : t('itineraryBuilder.map.openMaps')}
          </a>
        </>
      )}
    </div>
  )
}
