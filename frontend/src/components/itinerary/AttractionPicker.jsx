// Modal for adding attractions to one itinerary day. Reuses the Explore
// search endpoint (GET /api/attractions) with debounced live search; the
// top-rated places show before the user types. Stays open after each add so
// a whole day can be filled in one visit.

import { useEffect, useRef, useState } from 'react'
import { useTranslation } from 'react-i18next'
import AttractionImage from '../explore/AttractionImage'
import { fetchAttractions } from '../../services/attractions'

const SEARCH_DEBOUNCE_MS = 300
const RESULTS_PER_PAGE = 8

export default function AttractionPicker({ dayNumber, dateLabel, plannedIds, alreadyInDayIds = new Set(), onAdd, onClose }) {
  const { t } = useTranslation()
  const [searchInput, setSearchInput] = useState('')
  const [search, setSearch] = useState('')
  const [page, setPage] = useState(1)
  const [results, setResults] = useState([])
  const [pagination, setPagination] = useState(null)
  const [loading, setLoading] = useState(true)
  const [loadingMore, setLoadingMore] = useState(false)
  const [error, setError] = useState(false)
  const [addingId, setAddingId] = useState(null)
  const [justAddedId, setJustAddedId] = useState(null) // brief "✓ Added" flash
  const inputRef = useRef(null)

  useEffect(() => {
    inputRef.current?.focus()
  }, [])

  // Close on Escape, from anywhere in the dialog.
  useEffect(() => {
    const onKey = (event) => {
      if (event.key === 'Escape') onClose()
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [onClose])

  useEffect(() => {
    const timer = setTimeout(() => {
      setSearch(searchInput.trim())
      setPage(1)
    }, SEARCH_DEBOUNCE_MS)
    return () => clearTimeout(timer)
  }, [searchInput])

  useEffect(() => {
    let cancelled = false
    if (page === 1) setLoading(true)
    else setLoadingMore(true)
    setError(false)
    fetchAttractions({ search, sort: 'rating', page, perPage: RESULTS_PER_PAGE })
      .then((data) => {
        if (cancelled) return
        setResults((prev) => (page === 1 ? data.attractions : [...prev, ...data.attractions]))
        setPagination(data.pagination)
      })
      .catch(() => {
        if (!cancelled) setError(true)
      })
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
          setLoadingMore(false)
        }
      })
    return () => {
      cancelled = true
    }
  }, [search, page])

  const hasMore = pagination && pagination.page < pagination.total_pages

  const handleAdd = async (attraction) => {
    if (addingId) return
    setAddingId(attraction.id)
    try {
      await onAdd(attraction)
      // Confirm the add in place — the modal stays open for the next one.
      setJustAddedId(attraction.id)
      setTimeout(
        () => setJustAddedId((id) => (id === attraction.id ? null : id)),
        1500
      )
    } catch {
      // The builder already surfaces the failure via its save-status chip.
    } finally {
      setAddingId(null)
    }
  }

  return (
    <div className="it-modal-backdrop" onClick={onClose}>
      <div
        className="it-modal it-picker card"
        role="dialog"
        aria-modal="true"
        aria-labelledby="picker-title"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="it-modal-head">
          <h2 id="picker-title">
            {t('itineraryBuilder.picker.addToDay')} {dayNumber}
            {dateLabel && <span className="it-picker-date"> · {dateLabel}</span>}
          </h2>
          <button type="button" className="it-modal-close" onClick={onClose} aria-label={t('itineraryBuilder.picker.closeBtn')}>
            ✕
          </button>
        </div>

        <input
          ref={inputRef}
          type="search"
          className="input"
          value={searchInput}
          onChange={(e) => setSearchInput(e.target.value)}
          placeholder={t('itineraryBuilder.picker.searchPlaceholder')}
          aria-label={t('itineraryBuilder.picker.searchAria')}
        />

        <div className="it-picker-results">
          {loading ? (
            <div className="it-picker-state">
              <div className="spinner" />
            </div>
          ) : error ? (
            <p className="it-picker-note">{t('itineraryBuilder.picker.searchFailed')}</p>
          ) : results.length === 0 ? (
            <p className="it-picker-note">
              {t('itineraryBuilder.picker.noMatches')}
            </p>
          ) : (
          results.map((attraction) => {
              const inThisDay = alreadyInDayIds.has(attraction.id)
              const inOtherDay = !inThisDay && plannedIds.has(attraction.id)
              const justAdded = justAddedId === attraction.id
              return (
                <div key={attraction.id} className="it-picker-row">
                  <div className="it-picker-thumb">
                    <AttractionImage attraction={attraction} className="it-picker-img" />
                  </div>
                  <div className="it-picker-body">
                    <span className="it-picker-name">{attraction.name}</span>
                    <span className="it-picker-meta">
                      {attraction.category}
                      {attraction.avg_rating ? ` · ★ ${attraction.avg_rating.toFixed(1)}` : ''}
                    </span>
                  </div>
                  <button
                    type="button"
                    className={`btn ${
                      inThisDay
                        ? 'btn-ghost'
                        : inOtherDay
                          ? 'btn-ghost'
                          : 'btn-secondary'
                    } it-picker-add${
                      justAdded ? ' is-added' : ''
                    }`}
                    onClick={() => handleAdd(attraction)}
                    disabled={addingId === attraction.id || justAdded || inThisDay}
                    title={inThisDay ? `${attraction.name} is already in Day ${dayNumber}` : undefined}
                  >
                    {addingId === attraction.id
                      ? t('itineraryBuilder.picker.adding')
                      : justAdded
                        ? t('itineraryBuilder.picker.added')
                        : inThisDay
                          ? t('itineraryBuilder.picker.inThisDay')
                          : inOtherDay
                            ? t('itineraryBuilder.picker.addAgain')
                            : t('itineraryBuilder.picker.add')}
                  </button>
                </div>
              )
            })
          )}
          {hasMore && (
            <div className="it-picker-more">
              <button
                type="button"
                className="btn btn-ghost"
                onClick={() => setPage((p) => p + 1)}
                disabled={loadingMore}
              >
                {loadingMore ? t('itineraryBuilder.picker.loadingMore') : t('itineraryBuilder.picker.loadMoreBtn')}
              </button>
            </div>
          )}
        </div>

        <p className="it-picker-hint" dangerouslySetInnerHTML={{ __html: t('itineraryBuilder.picker.hint') }} />
      </div>
    </div>
  )
}
