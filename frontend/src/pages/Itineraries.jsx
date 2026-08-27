// My Itineraries — the trips list. Cards link into the Itinerary Builder;
// "Plan a new trip" opens a modal that creates the itinerary and jumps
// straight into the builder for it.

import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageContainer from '../components/layout/PageContainer'
import { attractionPhoto } from '../assets/photos'
import {
  createItinerary,
  deleteItinerary,
  fetchItineraries,
} from '../services/itineraries'
import { dayCount, formatTripRange } from '../utils/tripDates'
import '../styles/itinerary.css'

function todayIso(offsetDays = 0) {
  const d = new Date()
  d.setDate(d.getDate() + offsetDays)
  return d.toISOString().slice(0, 10)
}

/** Modal form: trip title + dates, with a live day-count readout. */
function NewTripModal({ onClose }) {
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [origin, setOrigin] = useState('')
  const [destination, setDestination] = useState('')
  const [stops, setStops] = useState([])
  const [description, setDescription] = useState('')
  const [startDate, setStartDate] = useState(todayIso())
  const [endDate, setEndDate] = useState(todayIso(2))
  const [tripType, setTripType] = useState('Solo')
  const [preferences, setPreferences] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)

  const days = dayCount(startDate, endDate)
  const datesInvalid = Boolean(startDate && endDate && !days)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!destination.trim() || datesInvalid || submitting) return
    setSubmitting(true)
    setError(null)
    
    // The title of the itinerary is the destination
    let title = destination.trim()
    if (origin.trim()) {
      title += ` from ${origin.trim()}`
    }

    try {
      const itinerary = await createItinerary({
        title: title.trim(),
        startLocation: origin.trim(),
        endLocation: destination.trim(),
        stops: stops.map(s => s.trim()).filter(s => s),
        description: description.trim(),
        startDate,
        endDate,
        is_ai_generated: true,
        tripType,
      })
      
      const fullPreferences = preferences.trim()
      // Navigate to the AI Trip Viewer 
      navigate(`/itineraries/${itinerary.id}`, { state: { initialPreferences: fullPreferences } })
    } catch (err) {
      setError(err?.response?.data?.error || t('itineraries.createError'))
      setSubmitting(false)
    }
  }

  return (
    <div className="it-modal-backdrop" onClick={onClose}>
      <div
        className="it-modal card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-trip-title"
        onClick={(e) => e.stopPropagation()}
        style={{ maxWidth: '600px' }}
      >
        <div className="it-modal-head">
          <h2 id="new-trip-title">{t('itineraries.modalTitle')}</h2>
          <button type="button" className="it-modal-close" onClick={onClose} aria-label={t('itineraries.closeBtn')}>
            ✕
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="it-date-row">
            <div className="field">
              <label className="label" htmlFor="trip-origin">{t('itineraries.startFrom')}</label>
              <input
                id="trip-origin"
                className="input"
                value={origin}
                onChange={(e) => setOrigin(e.target.value)}
                placeholder={t('itineraries.startFromPlaceholder')}
                maxLength={200}
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="trip-dest">{t('itineraries.to')}</label>
              <input
                id="trip-dest"
                className="input"
                value={destination}
                onChange={(e) => setDestination(e.target.value)}
                placeholder={t('itineraries.toPlaceholder')}
                maxLength={200}
                autoFocus
              />
            </div>
          </div>
          
          <div className="field">
            <label className="label">{t('itineraries.stopsLabel')}</label>
            {stops.map((stop, index) => (
              <div key={index} style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.5rem' }}>
                <input
                  className="input"
                  value={stop}
                  onChange={(e) => {
                    const newStops = [...stops]
                    newStops[index] = e.target.value
                    setStops(newStops)
                  }}
                  placeholder={t('itineraries.stopPlaceholder')}
                  maxLength={200}
                  style={{ flex: 1 }}
                />
                <button 
                  type="button" 
                  className="btn btn-ghost" 
                  onClick={() => setStops(stops.filter((_, i) => i !== index))}
                >
                  ✕
                </button>
              </div>
            ))}
            <button 
              type="button" 
              className="btn btn-ghost" 
              onClick={() => setStops([...stops, ''])}
              style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
            >
              {t('itineraries.addStopBtn')}
            </button>
          </div>

          <div className="field">
            <label className="label" htmlFor="trip-description">{t('itineraries.descriptionLabel')}</label>
            <textarea
              id="trip-description"
              className="input"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder={t('itineraries.descriptionPlaceholder')}
              rows={2}
            />
          </div>

          <div className="it-date-row">
            <div className="field">
              <label className="label" htmlFor="trip-start">{t('itineraries.startDate')}</label>
              <input
                id="trip-start"
                className="input"
                type="date"
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
              />
            </div>
            <div className="field">
              <label className="label" htmlFor="trip-end">{t('itineraries.toDate')}</label>
              <input
                id="trip-end"
                className="input"
                type="date"
                value={endDate}
                min={startDate || undefined}
                onChange={(e) => setEndDate(e.target.value)}
              />
            </div>
          </div>
          
          <div className="field">
            <label className="label" htmlFor="trip-type">Trip Type</label>
            <select
              id="trip-type"
              className="input"
              value={tripType}
              onChange={(e) => setTripType(e.target.value)}
            >
              <option value="Solo">Solo</option>
              <option value="Couple">Couple</option>
              <option value="Friends">Friends</option>
              <option value="Family">Family</option>
            </select>
          </div>

          <div className="field">
            <label className="label" htmlFor="trip-prefs">{t('itineraries.prefsLabel')}</label>
            <textarea
              id="trip-prefs"
              className="input"
              value={preferences}
              onChange={(e) => setPreferences(e.target.value)}
              placeholder={t('itineraries.prefsPlaceholder')}
              style={{ minHeight: '80px', resize: 'vertical' }}
            />
          </div>

          <p className={`it-days-hint ${datesInvalid ? 'it-days-hint-error' : ''}`} aria-live="polite">
            {datesInvalid
              ? t('itineraries.dateError')
              : days
                ? `${days} ${days === 1 ? t('itineraries.dayOfAdventure') : t('itineraries.daysOfAdventure')}`
                : t('itineraries.pickDates')}
          </p>

          {error && <div className="alert alert-error">{error}</div>}

          <div className="it-modal-actions">
            <button type="button" className="btn btn-ghost" onClick={onClose}>
              {t('itineraries.cancelBtn')}
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={!destination.trim() || datesInvalid || submitting}
            >
              {submitting ? t('itineraries.creatingBtn') : t('itineraries.createBtn')}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}

/** Real photos of the trip's own stops, matched by name — the card's cover. */
function tripCoverPhotos(previewStops, max = 3) {
  const photos = []
  const seen = new Set()
  for (const name of previewStops) {
    const photo = attractionPhoto({ name })
    if (photo && !seen.has(photo.src)) {
      seen.add(photo.src)
      photos.push(photo)
    }
    if (photos.length >= max) break
  }
  return photos
}

function TripCard({ itinerary, onDelete }) {
  const { t } = useTranslation()
  const days = dayCount(itinerary.start_date, itinerary.end_date)
  const range = formatTripRange(itinerary.start_date, itinerary.end_date)
  const covers = tripCoverPhotos(itinerary.preview_stops)

  const handleDelete = (event) => {
    event.preventDefault()
    event.stopPropagation()
    onDelete(itinerary)
  }

  return (
    <Link to={`/itineraries/${itinerary.id}`} className="trip-card card card-hover">
      <div className="trip-card-photos" aria-hidden="true">
        {covers.length > 0 ? (
          covers.map((photo) => (
            <img
              key={photo.src}
              src={photo.src}
              style={{ objectPosition: photo.position }}
              alt=""
              loading="lazy"
            />
          ))
        ) : (
          <span className="trip-card-photos-empty">🧭</span>
        )}
      </div>

      <div className="trip-card-body">
        <div className="trip-card-top">
          <div className="trip-card-badges">
            {days && <span className="badge badge-primary">{days} {days === 1 ? t('itineraries.dayCount') : t('itineraries.daysCount')}</span>}
            <span className="badge">
              {itinerary.item_count} {itinerary.item_count === 1 ? t('itineraries.placeCount') : t('itineraries.placesCount')}
            </span>
          </div>
          <button
            type="button"
            className="trip-card-delete"
            onClick={handleDelete}
            aria-label={t('itineraries.deleteAria', { title: itinerary.title })}
            title={t('itineraries.deleteTitle')}
          >
            <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M4 7h16M9 7V5a1 1 0 0 1 1-1h4a1 1 0 0 1 1 1v2m-8 0 1 13h8l1-13"
                stroke="currentColor"
                strokeWidth="1.8"
                strokeLinecap="round"
                strokeLinejoin="round"
              />
            </svg>
          </button>
        </div>

        <h3 className="trip-card-title">{itinerary.title}</h3>
        {range && <p className="trip-card-range">{range}</p>}

        {itinerary.preview_stops.length > 0 ? (
          <p className="trip-card-stops">
            {itinerary.preview_stops.join(' · ')}
            {itinerary.item_count > itinerary.preview_stops.length && ' · …'}
          </p>
        ) : (
          <p className="trip-card-stops trip-card-stops-empty">
            {t('itineraries.nothingPlanned')}
          </p>
        )}

        <span className="trip-card-cta" aria-hidden="true">
          {t('itineraries.openPlanner')}
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none">
            <path
              d="M5 12h14m0 0-6-6m6 6-6 6"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </span>
      </div>
    </Link>
  )
}

export default function Itineraries() {
  const { t } = useTranslation()
  const [itineraries, setItineraries] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(false)
  const [showModal, setShowModal] = useState(false)

  useEffect(() => {
    let cancelled = false
    fetchItineraries()
      .then((rows) => {
        if (!cancelled) setItineraries(rows)
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })
    return () => {
      cancelled = true
    }
  }, [])

  const handleDelete = async (itinerary) => {
    if (!window.confirm(t('itineraries.confirmDelete', { title: itinerary.title }))) return
    const previous = itineraries
    setItineraries((prev) => prev.filter((i) => i.id !== itinerary.id))
    try {
      await deleteItinerary(itinerary.id)
    } catch {
      setItineraries(previous) // deletion failed — put it back
    }
  }

  return (
    <PageContainer
      title={t('itineraries.pageTitle')}
      subtitle={t('itineraries.pageSubtitle')}
      actions={
        <button type="button" className="btn btn-primary" onClick={() => setShowModal(true)}>
          {t('itineraries.planNewBtn')}
        </button>
      }
    >
      {loading ? (
        <div className="loading-screen">
          <div className="spinner" />
          <p>{t('itineraries.loadingTrips')}</p>
        </div>
      ) : error ? (
        <div className="alert alert-error">
          {t('itineraries.loadError')}
        </div>
      ) : itineraries.length === 0 ? (
        <div className="explore-empty card">
          <span className="explore-empty-icon" aria-hidden="true">🧳</span>
          <h3>{t('itineraries.noTripsTitle')}</h3>
          <p>
            {t('itineraries.noTripsDesc')}
          </p>
          <button type="button" className="btn btn-primary" onClick={() => setShowModal(true)}>
            {t('itineraries.planNewCardBtn')}
          </button>
        </div>
      ) : (
        <div className="trip-grid">
          {itineraries.map((itinerary) => (
            <TripCard key={itinerary.id} itinerary={itinerary} onDelete={handleDelete} />
          ))}
        </div>
      )}

      {showModal && <NewTripModal onClose={() => setShowModal(false)} />}
    </PageContainer>
  )
}
