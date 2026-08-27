// Pre-login landing page — the first impression. A full-viewport photo hero
// with the value proposition and a search-shaped CTA, an editorial strip of
// destinations, the three AI capabilities, and a closing CTA band. All
// photography comes from the bundled scenes in assets/photos.js.

import { Link, useLocation } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Logo from '../components/layout/Logo'
import LanguageSwitcher from '../components/layout/LanguageSwitcher'
import { useAuth } from '../context/AuthContext'
import { scenes } from '../assets/photos'
import '../styles/landing.css'

const getWonders = (t) => [
  { scene: scenes.sigiriyaGround, name: t('landing.wonders.sigiriya.name'), region: t('landing.wonders.sigiriya.region') },
  { scene: scenes.nineArch, name: t('landing.wonders.nineArch.name'), region: t('landing.wonders.nineArch.region') },
  { scene: scenes.templeOfTooth, name: t('landing.wonders.templeOfTooth.name'), region: t('landing.wonders.templeOfTooth.region') },
  { scene: scenes.coconutTreeHill, name: t('landing.wonders.coconutTreeHill.name'), region: t('landing.wonders.coconutTreeHill.region') },
  { scene: scenes.leopard, name: t('landing.wonders.leopard.name'), region: t('landing.wonders.leopard.region') },
  { scene: scenes.galleFort, name: t('landing.wonders.galleFort.name'), region: t('landing.wonders.galleFort.region') },
  { scene: scenes.adamsPeak, name: t('landing.wonders.adamsPeak.name'), region: t('landing.wonders.adamsPeak.region') },
  { scene: scenes.dambulla, name: t('landing.wonders.dambulla.name'), region: t('landing.wonders.dambulla.region') },
]

const getFeatures = (t) => [
  {
    scene: scenes.adamsPeak,
    title: t('landing.features.f1.title'),
    copy: t('landing.features.f1.copy'),
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M12 3l1.9 5.3L19 10l-5.1 1.7L12 17l-1.9-5.3L5 10l5.1-1.7L12 3z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <path d="M18.5 15.5l.9 2.6 2.6.9-2.6.9-.9 2.6-.9-2.6-2.6-.9 2.6-.9.9-2.6z" fill="currentColor" />
      </svg>
    ),
  },
  {
    scene: scenes.templeOfTooth,
    title: t('landing.features.f2.title'),
    copy: t('landing.features.f2.copy'),
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M21 12a8 8 0 0 1-8 8H4l1.7-3.2A8 8 0 1 1 21 12z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <circle cx="9" cy="12" r="1" fill="currentColor" />
        <circle cx="13" cy="12" r="1" fill="currentColor" />
        <circle cx="17" cy="12" r="1" fill="currentColor" />
      </svg>
    ),
  },
  {
    scene: scenes.dambulla,
    title: t('landing.features.f3.title'),
    copy: t('landing.features.f3.copy'),
    icon: (
      <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
        <path
          d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"
          stroke="currentColor"
          strokeWidth="1.8"
          strokeLinejoin="round"
        />
        <circle cx="12" cy="14" r="3.5" stroke="currentColor" strokeWidth="1.8" />
      </svg>
    ),
  },
]

function SearchIcon() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
      <circle cx="11" cy="11" r="6.5" stroke="currentColor" strokeWidth="1.8" />
      <path d="m16 16 4.5 4.5" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" />
    </svg>
  )
}

export default function Landing() {
  const { isAuthenticated } = useAuth()
  const { state } = useLocation() // preserve a remembered destination through login
  const { t } = useTranslation()

  const wonders = getWonders(t)
  const features = getFeatures(t)

  return (
    <div className="landing">
      <header className="landing-nav">
        <Logo variant="bw" />
        <nav className="landing-nav-actions" aria-label="Account">
          <LanguageSwitcher className="btn-frost" />
          {isAuthenticated ? (
            <Link to="/" className="btn btn-white">
              {t('landing.openApp')}
            </Link>
          ) : (
            <>
              <Link to="/login" state={state} className="btn btn-frost">
                {t('landing.login')}
              </Link>
              <Link to="/signup" state={state} className="btn btn-white">
                {t('landing.getStarted')}
              </Link>
            </>
          )}
        </nav>
      </header>

      <section className="landing-hero">
        <img
          className="landing-hero-photo"
          src={scenes.stiltFishing.src}
          style={{ objectPosition: scenes.stiltFishing.position }}
          alt={scenes.stiltFishing.alt}
        />
        <div className="landing-hero-scrim" aria-hidden="true" />

        <div className="landing-hero-content">
          <span className="landing-kicker">{t('landing.heroKicker')}</span>
          <h1 className="landing-headline">{t('landing.heroHeadline')}</h1>
          <p className="landing-subhead">
            {t('landing.heroSubhead')}
          </p>

          <Link
            to={isAuthenticated ? '/explore' : '/signup'}
            state={state}
            className="landing-search"
            aria-label="Start exploring attractions"
          >
            <span className="landing-search-icon">
              <SearchIcon />
            </span>
            <span className="landing-search-text">
              {t('landing.searchPlaceholder')}
            </span>
            <span className="btn btn-primary landing-search-btn">{t('landing.exploreBtn')}</span>
          </Link>
        </div>
      </section>

      <section className="landing-section" aria-labelledby="wonders-title">
        <div className="landing-section-head">
          <div>
            <span className="landing-eyebrow">{t('landing.wondersEyebrow')}</span>
            <h2 id="wonders-title" className="landing-h2">
              {t('landing.wondersHeadline')}
            </h2>
          </div>
        </div>

        <div className="wonder-row">
          {wonders.map(({ scene, name, region }) => (
            <Link
              key={name}
              to={isAuthenticated ? '/explore' : '/signup'}
              className="wonder-card"
            >
              <img
                src={scene.src}
                style={{ objectPosition: scene.position }}
                alt={scene.alt}
                loading="lazy"
              />
              <div className="wonder-scrim" aria-hidden="true" />
              <span className="wonder-label">
                <span className="wonder-name">{name}</span>
                <span className="wonder-region">{region}</span>
              </span>
            </Link>
          ))}
        </div>
      </section>

      <section className="landing-section" aria-labelledby="features-title">
        <div className="landing-section-head">
          <div>
            <span className="landing-eyebrow">{t('landing.featuresEyebrow')}</span>
            <h2 id="features-title" className="landing-h2">
              {t('landing.featuresHeadline')}
            </h2>
          </div>
        </div>

        <div className="feature-grid">
          {features.map(({ scene, title, copy, icon }) => (
            <article key={title} className="feature-card">
              <div className="feature-photo">
                <img
                  src={scene.src}
                  style={{ objectPosition: scene.position }}
                  alt={scene.alt}
                  loading="lazy"
                />
              </div>
              <div className="feature-body">
                <span className="feature-icon">{icon}</span>
                <h3 className="feature-title">{title}</h3>
                <p className="feature-copy">{copy}</p>
              </div>
            </article>
          ))}
        </div>
      </section>

      <section className="landing-cta">
        <img
          src={scenes.whaleWatching.src}
          style={{ objectPosition: scenes.whaleWatching.position }}
          alt={scenes.whaleWatching.alt}
          loading="lazy"
        />
        <div className="landing-cta-scrim" aria-hidden="true" />
        <div className="landing-cta-content">
          <h2>{t('landing.ctaHeadline')}</h2>
          <p>{t('landing.ctaSubhead')}</p>
          <div className="landing-cta-actions">
            {isAuthenticated ? (
              <Link to="/" className="btn btn-white btn-lg">
                {t('landing.openApp')}
              </Link>
            ) : (
              <>
                <Link to="/signup" className="btn btn-white btn-lg">
                  {t('landing.createAccountBtn')}
                </Link>
                <Link to="/login" className="btn btn-frost btn-lg">
                  {t('landing.login')}
                </Link>
              </>
            )}
          </div>
        </div>
      </section>

      <footer className="landing-footer">
        <Logo variant="bw" />
        <span>{t('landing.copyright', { year: new Date().getFullYear() })}</span>
      </footer>
    </div>
  )
}
