// Avatar button + dropdown (profile, logout). Closes on outside click, Escape,
// or navigation. Initials come from the backend user's name, falling back to
// the email prefix.

import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { useAuth } from '../../context/AuthContext'

import { useTranslation } from 'react-i18next'

function initialsOf(user, firebaseUser) {
  const name = user?.name || firebaseUser?.email?.split('@')[0] || '?'
  const parts = name.trim().split(/\s+/)
  const first = parts[0]?.[0] ?? '?'
  const second = parts.length > 1 ? parts[parts.length - 1][0] : ''
  return (first + second).toUpperCase()
}

export default function UserMenu() {
  const { user, firebaseUser, logout } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const rootRef = useRef(null)

  useEffect(() => {
    if (!open) return
    function onPointerDown(e) {
      if (rootRef.current && !rootRef.current.contains(e.target)) setOpen(false)
    }
    function onKeyDown(e) {
      if (e.key === 'Escape') setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  async function handleLogout() {
    setOpen(false)
    await logout()
    navigate('/login')
  }

  const displayName = user?.name || firebaseUser?.email?.split('@')[0] || t('user.traveler')
  const email = user?.email || firebaseUser?.email || ''

  return (
    <div className="user-menu" ref={rootRef}>
      <button
        type="button"
        className="avatar-btn"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-label={t('user.accountMenu')}
        onClick={() => setOpen((v) => !v)}
      >
        <span className="avatar">{initialsOf(user, firebaseUser)}</span>
      </button>

      {open && (
        <div className="dropdown" role="menu">
          <div className="dropdown-header">
            <span className="dropdown-name">{displayName}</span>
            <span className="dropdown-email">{email}</span>
          </div>
          <Link
            to="/profile"
            className="dropdown-item"
            role="menuitem"
            onClick={() => setOpen(false)}
          >
            {t('user.profile')}
          </Link>
          <div className="dropdown-divider" role="separator" />
          <button
            type="button"
            className="dropdown-item dropdown-item-danger"
            role="menuitem"
            onClick={handleLogout}
          >
            {t('user.logout')}
          </button>
        </div>
      )}
    </div>
  )
}
