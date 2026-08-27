import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageContainer from '../components/layout/PageContainer'
import AttractionMap from '../components/explore/AttractionMap'
import StarRating from '../components/explore/StarRating'
import WeatherCard from '../components/weather/WeatherCard'
import { fetchHotel } from '../services/hotels'
import '../styles/explore.css'

function DetailSkeleton() {
  return (
    <div aria-busy="true" aria-label="Loading hotel">
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

export default function HotelDetail() {
  const { t, i18n } = useTranslation()
  const { id } = useParams()
  const [hotel, setHotel] = useState(null)
  const [error, setError] = useState(null)

  const load = () => {
    fetchHotel(id)
      .then(setHotel)
      .catch((err) => {
        setError(
          err?.response?.status === 404
            ? t('detail.hotel.notFound')
            : t('detail.hotel.loadError')
        )
      })
  }

  useEffect(() => {
    window.scrollTo(0, 0)
    setHotel(null)
    setError(null)
    load()
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
        {t('detail.hotel.backToExplore')}
      </Link>

      {error ? (
        <div className="explore-empty card">
          <span className="explore-empty-icon" aria-hidden="true">
            🛏️
          </span>
          <h3>{t('detail.hotel.errorTitle')}</h3>
          <p>{error}</p>
          <Link to="/explore" className="btn btn-primary">
            {t('detail.hotel.browseBtn')}
          </Link>
        </div>
      ) : !hotel ? (
        <DetailSkeleton />
      ) : (
        <>
          <section className="detail-media">
            <img
              src={hotel.image_url || 'https://images.unsplash.com/photo-1566073771259-6a8506099945?auto=format&fit=crop&q=80&w=1200'}
              alt={hotel.name}
              className="detail-media-img"
            />
            <div className="detail-media-scrim" aria-hidden="true" />
            <div className="detail-media-caption">
              <span className="media-badge" style={{ textTransform: 'capitalize' }}>
                {hotel.budget_tier || t('detail.hotel.fallbackBudget')}
              </span>
              <h1>{hotel.name}</h1>
              <div className="rating-line detail-rating-line">
                <StarRating value={hotel.avg_rating} size={18} />
                <span className="rating-value">
                  {hotel.avg_rating ? hotel.avg_rating.toFixed(1) : t('detail.hotel.newRating')}
                </span>
                <span className="rating-count">
                  · 📍 {hotel.location}
                </span>
              </div>
            </div>
          </section>

          <div className="detail-layout">
            <div className="detail-main">
              <section className="detail-about">
                <h2 className="detail-section-title">{t('detail.hotel.about')}</h2>
                <p className="detail-description">{hotel.description}</p>
              </section>
            </div>

            <aside className="detail-aside">
              <section className="card detail-map-card">
                <div className="detail-map-head">
                  <h2 className="detail-section-title">{t('detail.hotel.locationSection')}</h2>
                </div>
                {/* Reusing AttractionMap; it just needs a latitude and longitude property which hotel provides */}
                <AttractionMap attraction={hotel} />
                <dl className="geo-list">
                  <div className="geo-row">
                    <dt>{t('detail.hotel.latitude')}</dt>
                    <dd>{hotel.latitude?.toFixed(4)}</dd>
                  </div>
                  <div className="geo-row">
                    <dt>{t('detail.hotel.longitude')}</dt>
                    <dd>{hotel.longitude?.toFixed(4)}</dd>
                  </div>
                  <div className="geo-row">
                    <dt>{t('detail.hotel.locationField')}</dt>
                    <dd>{hotel.location}</dd>
                  </div>
                  <div className="geo-row">
                    <dt>{t('detail.hotel.budgetTier')}</dt>
                    <dd style={{ textTransform: 'capitalize' }}>{hotel.budget_tier}</dd>
                  </div>
                </dl>
              </section>

              <section className="card card-pad">
                <h2 className="detail-section-title">{t('detail.hotel.weather')}</h2>
                <WeatherCard
                  latitude={hotel.latitude}
                  longitude={hotel.longitude}
                  placeName={hotel.name}
                />
              </section>
            </aside>
          </div>
        </>
      )}
    </PageContainer>
  )
}
