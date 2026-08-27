// App footer — brand, quick links, and project meta.

import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import Logo from './Logo'

export default function Footer() {
  const { t } = useTranslation()

  return (
    <footer className="footer">
      <div className="footer-inner">
        <div className="footer-brand">
          <Logo />
          <p className="footer-tagline">
            {t('footer.tagline')}
          </p>
        </div>

        <nav className="footer-col" aria-label={t('footer.discover')}>
          <span className="footer-heading">{t('footer.discover')}</span>
          <Link to="/explore">{t('nav.explore')}</Link>
          <Link to="/itineraries">{t('nav.itineraries')}</Link>
          <Link to="/chat">{t('footer.askTourMate')}</Link>
        </nav>

        <nav className="footer-col" aria-label={t('footer.account')}>
          <span className="footer-heading">{t('footer.account')}</span>
          <Link to="/profile">{t('user.profile')}</Link>
          <Link to="/">{t('nav.home')}</Link>
        </nav>
      </div>

      <div className="footer-bottom">
        <span>© {new Date().getFullYear()} TourMateAI · A CIS6035 project</span>
        <span>{t('footer.madeFor')}</span>
      </div>
    </footer>
  )
}
