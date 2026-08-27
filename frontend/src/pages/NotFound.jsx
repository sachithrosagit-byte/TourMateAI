// 404 page for unknown routes. Rendered inside the app shell (navbar + footer),
// so a lost authenticated user still has full navigation to get back on track.

import { Link } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import PageContainer from '../components/layout/PageContainer'

export default function NotFound() {
  const { t } = useTranslation()
  return (
    <PageContainer width="narrow">
      <div className="card error-state">
        <span className="error-state-code" aria-hidden="true">404</span>
        <h1 className="error-state-title">{t('notFound.title')}</h1>
        <p className="error-state-text">
          {t('notFound.text')}
        </p>
        <div className="error-state-actions">
          <Link to="/" className="btn btn-primary">
            {t('notFound.backBtn')}
          </Link>
          <Link to="/explore" className="btn btn-ghost">
            {t('notFound.exploreBtn')}
          </Link>
        </div>
      </div>
    </PageContainer>
  )
}
