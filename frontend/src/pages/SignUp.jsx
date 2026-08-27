// Sign-up page — email/password, wrapped in the AuthLayout brand shell.

import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../context/AuthContext'
import AuthLayout from '../components/layout/AuthLayout'

export default function SignUp() {
  const { signup } = useAuth()
  const navigate = useNavigate()
  const { t } = useTranslation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  async function handleSubmit(e) {
    e.preventDefault()
    setError('')
    setSubmitting(true)
    try {
      await signup(email, password)
      // Firebase signs the user in on success; land them on the app home.
      navigate('/', { replace: true })
    } catch (err) {
      setError(err.message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthLayout>
      <div className="auth-card">
        <h2 className="auth-title">{t('auth.signupTitle')}</h2>
        <p className="auth-lead">
          {t('auth.signupLead')}
        </p>

        {error && (
          <div className="alert alert-error" role="alert">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label className="label" htmlFor="email">{t('auth.emailLabel')}</label>
            <input
              id="email"
              className="input"
              type="email"
              placeholder={t('auth.emailPlaceholder')}
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
            />
          </div>

          <div className="field">
            <label className="label" htmlFor="password">{t('auth.passwordLabel')}</label>
            <input
              id="password"
              className="input"
              type="password"
              placeholder={t('auth.signupPasswordPlaceholder')}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              minLength={6}
            />
            <p className="hint">{t('auth.passwordHint')}</p>
          </div>

          <button type="submit" className="btn btn-primary btn-lg btn-block" disabled={submitting}>
            {submitting ? t('auth.creatingAccountBtn') : t('auth.createAccountBtn')}
          </button>
        </form>

        <p className="auth-switch">
          {t('auth.alreadyHaveAccount')} <Link to="/login">{t('auth.loginLink')}</Link>
        </p>
      </div>
    </AuthLayout>
  )
}
