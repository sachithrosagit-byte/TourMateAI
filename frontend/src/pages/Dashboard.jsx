// Dashboard — the authenticated home, laid out like a curated travel magazine:
// a time-of-day photo hero, quick actions into the three AI features, then
// three data sections:
//   - Recommended for you  → GET /api/recommendations/mock (placeholder until
//                            the real engine lands; see services/recommendations.js)
//                            First pick runs as the "lead story", rest support.
//   - Continue planning    → GET /api/itineraries (rows with photo thumbnails)
//   - Trending attractions → GET /api/attractions?sort=rating (ranked tiles)
// Each section loads independently so one failure never blanks the page.

import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import PageContainer from '../components/layout/PageContainer'
import AttractionImage from '../components/explore/AttractionImage'
import { attractionPhoto, scenes } from '../assets/photos'
import { fetchAttractions } from '../services/attractions'
import { fetchItineraries } from '../services/itineraries'
import { fetchRecommendations } from '../services/recommendations'
import '../styles/pages.css'
import '../styles/explore.css'
import '../styles/dashboard.css'

import { useTranslation } from 'react-i18next'

const SECTION_SIZE = 4

// The hero photo follows the clock — the app's whole pitch is context-aware.
function heroSceneForHour(hour) {
  if (hour >= 5 && hour < 11) return scenes.sigiriyaAerial
  if (hour >= 11 && hour < 16) return scenes.nineArch
  if (hour >= 16 && hour < 19) return scenes.stiltFishing
  return scenes.galleLighthouse
}

function greetingForHour(hour, t) {
  if (hour >= 5 && hour < 12) return t('dashboard.greetings.morning')
  if (hour >= 12 && hour < 17) return t('dashboard.greetings.afternoon')
  return t('dashboard.greetings.evening')
}

const getQuickActions = (t) => [
  {
    to: '/itineraries',
    title: t('dashboard.quickActions.planTitle'),
    sub: t('dashboard.quickActions.planSub'),
    accent: 'qa-plan',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <rect x="4.5" y="5.5" width="15" height="14" rx="2.3" stroke="currentColor" strokeWidth="1.8" />
        <path d="M8 3.5v4M16 3.5v4M4.5 10.5h15" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
        <path d="M8.5 14.5h3" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: '/chat',
    title: t('dashboard.quickActions.askTitle'),
    sub: t('dashboard.quickActions.askSub'),
    accent: 'qa-chat',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M4.5 6.8A2.3 2.3 0 0 1 6.8 4.5h10.4a2.3 2.3 0 0 1 2.3 2.3v7.4a2.3 2.3 0 0 1-2.3 2.3H9.6l-3.8 3v-3H6.8a2.3 2.3 0 0 1-2.3-2.3V6.8Z"
          stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"
        />
        <path d="M8.5 9.5h7M8.5 12.5h4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
      </svg>
    ),
  },
  {
    to: '/identify',
    title: t('dashboard.quickActions.identifyTitle'),
    sub: t('dashboard.quickActions.identifySub'),
    accent: 'qa-identify',
    icon: (
      <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M4.5 8.3A2.3 2.3 0 0 1 6.8 6h1.4l1.3-1.7a1.5 1.5 0 0 1 1.2-.6h2.6a1.5 1.5 0 0 1 1.2.6L15.8 6h1.4a2.3 2.3 0 0 1 2.3 2.3v8.4a2.3 2.3 0 0 1-2.3 2.3H6.8a2.3 2.3 0 0 1-2.3-2.3V8.3Z"
          stroke="currentColor" strokeWidth="1.8" strokeLinejoin="round"
        />
        <circle cx="12" cy="12.3" r="3.2" stroke="currentColor" strokeWidth="1.8" />
      </svg>
    ),
  },
]

function ArrowIcon() {
  return (
    <svg width="15" height="15" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <path d="M5 12h14m0 0-6-6m6 6-6 6" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  )
}

// Section wrapper: heading + optional "view all" link, consistent spacing.
function DashSection({ title, hint, linkTo, linkLabel, children }) {
  return (
    <section className="dash-section" aria-label={title}>
      <div className="dash-section-head">
        <div>
          <h2 className="dash-section-title">{title}</h2>
          {hint && <p className="dash-section-hint">{hint}</p>}
        </div>
        {linkTo && (
          <Link to={linkTo} className="dash-section-link">
            {linkLabel}
            <ArrowIcon />
          </Link>
        )}
      </div>
      {children}
    </section>
  )
}

// Skeletons that mirror the editorial layouts they stand in for.
function RecSkeleton() {
  return (
    <div className="rec-editorial" aria-busy="true">
      <div className="skeleton rec-feature-skeleton" />
      <div className="rec-side">
        {Array.from({ length: 3 }, (_, i) => (
          <div key={i} className="skeleton rec-mini-skeleton" />
        ))}
      </div>
    </div>
  )
}

function TrendSkeleton() {
  return (
    <div className="trend-row" aria-busy="true">
      {Array.from({ length: SECTION_SIZE }, (_, i) => (
        <div key={i} className="skeleton trend-skeleton" />
      ))}
    </div>
  )
}

function SectionError({ children }) {
  return <p className="dash-section-error">⚠️ {children}</p>
}

function formatDates(itinerary, t) {
  if (!itinerary.start_date) return t('dashboard.itineraries.datesNotSet')
  const opts = { day: 'numeric', month: 'short' }
  const start = new Date(itinerary.start_date).toLocaleDateString(undefined, opts)
  if (!itinerary.end_date) return start
  const end = new Date(itinerary.end_date).toLocaleDateString(undefined, opts)
  return `${start} – ${end}`
}

export default function Dashboard() {
  const { user, firebaseUser } = useAuth()
  const { t, i18n } = useTranslation()
  const name = user?.name || firebaseUser?.email?.split('@')[0] || t('user.traveler')
  const hasInterests = (user?.preferences?.interests || []).length > 0

  const hour = new Date().getHours()
  const heroScene = heroSceneForHour(hour)
  const today = new Date().toLocaleDateString(undefined, {
    weekday: 'long',
    day: 'numeric',
    month: 'long',
  })

  // Per-section state: null = loading, [] = loaded empty, 'error' = failed.
  const [recommended, setRecommended] = useState(null)
  const [itineraries, setItineraries] = useState(null)
  const [trending, setTrending] = useState(null)

  useEffect(() => {
    let cancelled = false
    const load = (promise, setter) =>
      promise
        .then((data) => !cancelled && setter(data))
        .catch(() => !cancelled && setter('error'))

    load(fetchRecommendations({ limit: SECTION_SIZE }), setRecommended)
    load(fetchItineraries(), setItineraries)
    load(
      fetchAttractions({ sort: 'rating', perPage: SECTION_SIZE }).then(
        (data) => data.attractions
      ),
      setTrending
    )

    return () => {
      cancelled = true
    }
  }, [i18n.language])

  return (
    <PageContainer>
      <section className="dash-hero">
        <img
          className="dash-hero-photo"
          src={heroScene.src}
          style={{ objectPosition: heroScene.position }}
          alt=""
          aria-hidden="true"
        />
        <div className="dash-hero-scrim" aria-hidden="true" />
        <div className="dash-hero-content">
          <span className="dash-hero-date">{today}</span>
          <h1 className="dash-greeting">
            {greetingForHour(hour, t)}, <span className="dash-name">{name}</span>.
          </h1>
          <p className="dash-lead">
            {t('dashboard.heroLead')}
          </p>
        </div>
      </section>

      <section className="qa-row" aria-label="Quick actions">
        {getQuickActions(t).map((qa) => (
          <Link key={qa.to} to={qa.to} className={`card card-hover qa-card ${qa.accent}`}>
            <span className="qa-icon">{qa.icon}</span>
            <span className="qa-text">
              <span className="qa-title">{qa.title}</span>
              <span className="qa-sub">{qa.sub}</span>
            </span>
            <span className="qa-arrow" aria-hidden="true">
              <ArrowIcon />
            </span>
          </Link>
        ))}
      </section>

      <DashSection
        title={t('dashboard.recommendations.title')}
        hint={
          hasInterests
            ? t('dashboard.recommendations.hintPersonalized')
            : t('dashboard.recommendations.hintGeneric')
        }
        linkTo="/profile"
        linkLabel={t('dashboard.recommendations.link')}
      >
        {recommended === null ? (
          <RecSkeleton />
        ) : recommended === 'error' ? (
          <SectionError>{t('dashboard.recommendations.error')}</SectionError>
        ) : recommended.length === 0 ? (
          <p className="dash-section-error">
            {t('dashboard.recommendations.empty')}
          </p>
        ) : (
          <div className="rec-editorial">
            {/* Lead story: the top pick runs big, caption over the photo. */}
            <Link to={`/explore/${recommended[0].id}`} className="rec-feature">
              <AttractionImage
                attraction={recommended[0]}
                className="rec-feature-img"
              />
              <div className="rec-feature-scrim" aria-hidden="true" />
              <div className="rec-feature-caption">
                <span className="media-badge">{recommended[0].category}</span>
                <h3 className="rec-feature-name">{recommended[0].name}</h3>
                {recommended[0].reason && (
                  <p className="rec-feature-reason">
                    <span aria-hidden="true">✦</span> {recommended[0].reason}
                  </p>
                )}
              </div>
            </Link>

            {/* Supporting picks: compact photo rows. */}
            <div className="rec-side">
              {recommended.slice(1).map((rec) => (
                <Link key={rec.id} to={`/explore/${rec.id}`} className="rec-mini">
                  <AttractionImage attraction={rec} className="rec-mini-img" />
                  <span className="rec-mini-text">
                    <span className="rec-mini-name">{rec.name}</span>
                    {rec.reason && (
                      <span className="rec-mini-reason">{rec.reason}</span>
                    )}
                  </span>
                  <span className="rec-mini-arrow" aria-hidden="true">
                    <ArrowIcon />
                  </span>
                </Link>
              ))}
            </div>
          </div>
        )}
      </DashSection>

      <DashSection
        title={t('dashboard.itineraries.title')}
        hint={t('dashboard.itineraries.hint')}
        linkTo={itineraries?.length ? '/itineraries' : undefined}
        linkLabel={t('dashboard.itineraries.link')}
      >
        {itineraries === null ? (
          <div className="itinerary-row-list" aria-busy="true">
            <div className="card itinerary-row skeleton" style={{ height: '4.5rem' }} />
          </div>
        ) : itineraries === 'error' ? (
          <SectionError>{t('dashboard.itineraries.error')}</SectionError>
        ) : itineraries.length === 0 ? (
          <div className="card dash-empty">
            <span className="dash-empty-icon" aria-hidden="true">🧳</span>
            <div className="dash-empty-text">
              <h3>{t('dashboard.itineraries.emptyTitle')}</h3>
              <p>{t('dashboard.itineraries.emptyDesc')}</p>
            </div>
            <Link to="/itineraries" className="btn btn-primary">
              {t('dashboard.itineraries.emptyBtn')}
            </Link>
          </div>
        ) : (
          <div className="itinerary-row-list">
            {itineraries.map((it) => {
              // First stop that has a bundled photo becomes the trip thumbnail.
              const thumb = (it.preview_stops || [])
                .map((stop) => attractionPhoto({ name: stop }))
                .find(Boolean)
              return (
                <Link key={it.id} to="/itineraries" className="card card-hover itinerary-row">
                  {thumb ? (
                    <img
                      className="itinerary-row-thumb"
                      src={thumb.src}
                      style={{ objectPosition: thumb.position }}
                      alt=""
                      aria-hidden="true"
                    />
                  ) : (
                    <span className="itinerary-row-icon" aria-hidden="true">🗺️</span>
                  )}
                  <span className="itinerary-row-text">
                    <span className="itinerary-row-title">{it.title}</span>
                    <span className="itinerary-row-meta">
                      {formatDates(it, t)} · {it.item_count}{' '}
                      {it.item_count === 1 ? t('dashboard.itineraries.place') : t('dashboard.itineraries.places')}
                      {it.preview_stops.length > 0 && (
                        <> · {it.preview_stops.join(' · ')}</>
                      )}
                    </span>
                  </span>
                  <span className="itinerary-row-arrow" aria-hidden="true">
                    <ArrowIcon />
                  </span>
                </Link>
              )
            })}
          </div>
        )}
      </DashSection>

      <DashSection
        title={t('dashboard.trending.title')}
        hint={t('dashboard.trending.hint')}
        linkTo="/explore"
        linkLabel={t('dashboard.trending.link')}
      >
        {trending === null ? (
          <TrendSkeleton />
        ) : trending === 'error' ? (
          <SectionError>{t('dashboard.trending.error')}</SectionError>
        ) : trending.length === 0 ? (
          <p className="dash-section-error">{t('dashboard.trending.empty')}</p>
        ) : (
          <div className="trend-row">
            {trending.map((attraction, i) => (
              <Link
                key={attraction.id}
                to={`/explore/${attraction.id}`}
                className="trend-card"
                style={{ animationDelay: `${i * 60}ms` }}
              >
                <AttractionImage attraction={attraction} className="trend-img" />
                <div className="trend-scrim" aria-hidden="true" />
                <span className="trend-rank" aria-hidden="true">
                  {String(i + 1).padStart(2, '0')}
                </span>
                <span className="trend-label">
                  <span className="trend-name">{attraction.name}</span>
                  <span className="trend-meta">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
                      <path d="M12 2l2.9 6.3 6.9.8-5.1 4.7 1.4 6.8-6.1-3.5-6.1 3.5 1.4-6.8L2.2 9.1l6.9-.8L12 2z" />
                    </svg>
                    {attraction.avg_rating ? attraction.avg_rating.toFixed(1) : t('dashboard.trending.newRating')}
                    {' · '}
                    {attraction.category}
                  </span>
                </span>
              </Link>
            ))}
          </div>
        )}
      </DashSection>
    </PageContainer>
  )
}
