// Attraction detail — full-bleed image banner with name/rating overlay, then
// a two-column layout: description + reviews (with a rating/comment form) on
// the left, location card (embedded Google Map) on the right. Opening the page
// logs a `view` interaction for the recommender.

import { useEffect, useRef, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageContainer from '../components/layout/PageContainer'
import AttractionImage from '../components/explore/AttractionImage'
import AttractionMap from '../components/explore/AttractionMap'
import StarRating from '../components/explore/StarRating'
import WeatherCard from '../components/weather/WeatherCard'
import NearbyAttractions from '../components/explore/NearbyAttractions'
import {
  fetchAttraction,
  logInteraction,
  submitFeedback,
} from '../services/attractions'
import '../styles/explore.css'

const STAR_PATH =
  'M12 2.5l2.94 5.95 6.56 0.96-4.75 4.63 1.12 6.54L12 17.5l-5.87 3.08 1.12-6.54L2.5 9.41l6.56-0.96L12 2.5Z'

function formatDate(iso) {
  if (!iso) return ''
  const date = new Date(iso)
  return date.toLocaleDateString(undefined, {
    day: 'numeric',
    month: 'short',
    year: 'numeric',
  })
}

// Interactive 1–5 star picker for the review form.
function StarPicker({ value, onChange }) {
  const [hovered, setHovered] = useState(0)
  const active = hovered || value

  const { t } = useTranslation()
  return (
    <div className="star-picker" role="radiogroup" aria-label={t('detail.attraction.yourRatingAria')}>
      {[1, 2, 3, 4, 5].map((star) => (
        <button
          key={star}
          type="button"
          role="radio"
          aria-checked={value === star}
          aria-label={`${star} ${star > 1 ? t('detail.attraction.stars') : t('detail.attraction.star')}`}
          className={`star-picker-btn${star <= active ? ' on' : ''}`}
          onClick={() => onChange(star)}
          onMouseEnter={() => setHovered(star)}
          onMouseLeave={() => setHovered(0)}
        >
          <svg width="26" height="26" viewBox="0 0 24 24" aria-hidden="true">
            <path d={STAR_PATH} fill="currentColor" />
          </svg>
        </button>
      ))}
    </div>
  )
}

function ReviewForm({ attractionId, onSubmitted }) {
  const { t } = useTranslation()
  const [rating, setRating] = useState(0)
  const [comment, setComment] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState(null)
  const [saved, setSaved] = useState(false)

  const handleSubmit = async (event) => {
    event.preventDefault()
    if (!rating) {
      setError(t('detail.attraction.pickStar'))
      return
    }
    setBusy(true)
    setError(null)
    try {
      await submitFeedback(attractionId, {
        rating,
        comment: comment.trim() || null,
      })
      setSaved(true)
      setComment('')
      setRating(0)
      onSubmitted()
    } catch {
      setError(t('detail.attraction.saveReviewError'))
    } finally {
      setBusy(false)
    }
  }

  return (
    <form className="review-form" onSubmit={handleSubmit}>
      <h3>{t('detail.attraction.shareExperience')}</h3>
      <p className="review-form-hint">
        {t('detail.attraction.reviewHint')}
      </p>

      <StarPicker
        value={rating}
        onChange={(star) => {
          setRating(star)
          setSaved(false)
          setError(null)
        }}
      />

      <textarea
        className="input review-textarea"
        rows="3"
        value={comment}
        onChange={(e) => {
          setComment(e.target.value)
          setSaved(false)
        }}
        placeholder={t('detail.attraction.commentPlaceholder')}
        aria-label={t('detail.attraction.commentAria')}
      />

      {error && <div className="alert alert-error">{error}</div>}
      {saved && !error && (
        <div className="alert alert-success">{t('detail.attraction.reviewSaved')}</div>
      )}

      <button type="submit" className="btn btn-primary" disabled={busy}>
        {busy ? t('detail.attraction.savingBtn') : t('detail.attraction.submitBtn')}
      </button>
    </form>
  )
}

function DetailSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading attraction">
      <div className="skeleton detail-media-skeleton" />
      <div className="detail-layout">
        <div className="detail-main">
          <div className="card card-pad">
            <div className="skeleton skeleton-line" style={{ width: '40%', height: '1.4rem' }} />
            <div className="skeleton skeleton-line" style={{ width: '100%' }} />
            <div className="skeleton skeleton-line" style={{ width: '92%' }} />
            <div className="skeleton skeleton-line" style={{ width: '65%' }} />
          </div>
        </div>
        <aside className="detail-aside">
          <div className="card card-pad">
            <div className="skeleton skeleton-line" style={{ width: '50%', height: '1.4rem' }} />
            <div className="skeleton detail-map-skeleton" />
          </div>
        </aside>
      </div>
    </div>
  )
}

export default function AttractionDetail() {
  const { t, i18n } = useTranslation()
  const { id } = useParams()
  const [attraction, setAttraction] = useState(null)
  const [error, setError] = useState(null)
  const viewLogged = useRef(null)

  const load = () => {
    fetchAttraction(id)
      .then(setAttraction)
      .catch((err) => {
        setError(
          err?.response?.status === 404
            ? t('detail.attraction.notFound')
            : t('detail.attraction.loadError')
        )
      })
  }

  useEffect(() => {
    setAttraction(null)
    setError(null)
    load()
    // Log the view once per attraction (guards StrictMode's double effect).
    if (viewLogged.current !== id) {
      viewLogged.current = id
      logInteraction(Number(id), 'view')
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id, i18n.language])

  return (
    <PageContainer>
      <Link to="/explore" className="detail-back">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" aria-hidden="true">
          <path
            d="M19 12H5m0 0 6 6m-6-6 6-6"
            stroke="currentColor"
            strokeWidth="2"
            strokeLinecap="round"
            strokeLinejoin="round"
          />
        </svg>
        {t('detail.attraction.backToExplore')}
      </Link>

      {error ? (
        <div className="explore-empty card">
          <span className="explore-empty-icon" aria-hidden="true">
            🧭
          </span>
          <h3>{t('detail.attraction.errorTitle')}</h3>
          <p>{error}</p>
          <Link to="/explore" className="btn btn-primary">
            {t('detail.attraction.browseBtn')}
          </Link>
        </div>
      ) : !attraction ? (
        <DetailSkeleton />
      ) : (
        <>
          <section className="detail-media">
            <AttractionImage attraction={attraction} className="detail-media-img" />
            <div className="detail-media-scrim" aria-hidden="true" />
            <div className="detail-media-caption">
              <span className="media-badge">{attraction.category}</span>
              <h1>{attraction.name}</h1>
              <div className="rating-line detail-rating-line">
                <StarRating value={attraction.avg_rating} size={18} />
                <span className="rating-value">
                  {attraction.avg_rating ? attraction.avg_rating.toFixed(1) : t('detail.attraction.newRating')}
                </span>
                <span className="rating-count">
                  · {attraction.rating_count}{' '}
                  {attraction.rating_count === 1 ? t('detail.attraction.reviewCount') : t('detail.attraction.reviewsCount')}
                </span>
              </div>
            </div>
          </section>

          <div className="detail-layout">
            <div className="detail-main">
              <section className="detail-about">
                <h2 className="detail-section-title">{t('detail.attraction.about')}</h2>
                <p className="detail-description">{attraction.description}</p>
              </section>

              <section className="detail-reviews">
                <h2 className="detail-section-title">{t('detail.attraction.feedback')}</h2>

                {attraction.reviews.length === 0 ? (
                  <p className="reviews-empty">
                    {t('detail.attraction.noReviews')}
                  </p>
                ) : (
                  <ul className="review-list" role="list">
                    {attraction.reviews.map((review) => (
                      <li key={review.id} className="review-item">
                        <div className="review-avatar" aria-hidden="true">
                          {(review.user_name || 'T').charAt(0).toUpperCase()}
                        </div>
                        <div className="review-body">
                          <div className="review-head">
                            <span className="review-author">
                              {review.user_name || 'Traveler'}
                            </span>
                            <span className="review-date">
                              {formatDate(review.created_at)}
                            </span>
                          </div>
                          <StarRating value={review.rating} size={13} />
                          {review.comment && (
                            <p className="review-comment">{review.comment}</p>
                          )}
                        </div>
                      </li>
                    ))}
                  </ul>
                )}

                <ReviewForm attractionId={attraction.id} onSubmitted={load} />
              </section>
            </div>

            <aside className="detail-aside">
              {/* Map sits flush inside its card so the embed reads as part of
                  the layout, not a bolted-on widget. */}
              <section className="card detail-map-card">
                <div className="detail-map-head">
                  <h2 className="detail-section-title">{t('detail.attraction.location')}</h2>
                </div>
                <AttractionMap attraction={attraction} />
                <dl className="geo-list">
                  <div className="geo-row">
                    <dt>{t('detail.attraction.latitude')}</dt>
                    <dd>{attraction.latitude?.toFixed(4)}</dd>
                  </div>
                  <div className="geo-row">
                    <dt>{t('detail.attraction.longitude')}</dt>
                    <dd>{attraction.longitude?.toFixed(4)}</dd>
                  </div>
                  <div className="geo-row">
                    <dt>{t('detail.attraction.category')}</dt>
                    <dd>{attraction.category}</dd>
                  </div>
                </dl>
              </section>

              <section className="card card-pad">
                <h2 className="detail-section-title">{t('detail.attraction.weather')}</h2>
                <WeatherCard
                  latitude={attraction.latitude}
                  longitude={attraction.longitude}
                  placeName={attraction.name}
                />
              </section>
            </aside>
          </div>
          
          {/* Nearby Locations Section */}
          <NearbyAttractions attractionId={attraction.id} />
        </>
      )}
    </PageContainer>
  )
}
