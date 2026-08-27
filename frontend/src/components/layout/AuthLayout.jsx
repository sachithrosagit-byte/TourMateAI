// Layout for the public auth pages (login / sign-up): a full-bleed Sigiriya
// landscape photo with the brand and headline over a dark scrim on the left,
// form card on clean white on the right. On mobile the photo collapses to a
// hero banner that the form card overlaps.

import { useTranslation } from 'react-i18next'
import Logo from './Logo'
import LanguageSwitcher from './LanguageSwitcher'
import sigiriyaPhoto from '../../assets/sigiriya.jpg'
import './auth.css'

export default function AuthLayout({ children }) {
  const { t } = useTranslation()

  return (
    <div className="auth-layout">
      <aside className="auth-brand-panel">
        <img
          className="auth-photo"
          src={sigiriyaPhoto}
          alt="Sigiriya rock fortress rising above the jungle at sunrise, Sri Lanka"
        />
        <div className="auth-photo-scrim" aria-hidden="true" />

        <div className="auth-brand-top" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Logo size="lg" variant="bw" />
          <LanguageSwitcher className="btn-frost" />
        </div>

        <div className="auth-brand-copy">
          <span className="auth-location">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true">
              <path d="M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 9.5A2.5 2.5 0 1 1 12 6.5a2.5 2.5 0 0 1 0 5z" />
            </svg>
            {t('auth.sigiriyaLocation')}
          </span>
          <h1 className="auth-headline">
            {t('auth.headline')}
          </h1>
          <p className="auth-subhead">
            {t('auth.subhead')}
          </p>
        </div>
      </aside>

      <main className="auth-form-panel">{children}</main>
    </div>
  )
}
