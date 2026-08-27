// Slide-in navigation drawer for small screens. Overlay click, Escape, or
// choosing a link closes it. Body scroll is locked while open.

import { useEffect } from 'react'
import { NavLink, useNavigate } from 'react-router-dom'
import { useTranslation } from 'react-i18next'
import { useAuth } from '../../context/AuthContext'
import useNavItems from '../../hooks/useNavItems'
import Logo from './Logo'

export default function MobileDrawer({ open, onClose }) {
  const navItems = useNavItems()
  const { user, firebaseUser, logout } = useAuth()
  const { t } = useTranslation()
  const navigate = useNavigate()

  useEffect(() => {
    if (!open) return
    document.body.style.overflow = 'hidden'
    function onKeyDown(e) {
      if (e.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.body.style.overflow = ''
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open, onClose])

  async function handleLogout() {
    onClose()
    await logout()
    navigate('/login')
  }

  return (
    <>
      <div
        className={open ? 'drawer-overlay drawer-overlay-open' : 'drawer-overlay'}
        onClick={onClose}
        aria-hidden="true"
      />
      <aside
        className={open ? 'drawer drawer-open' : 'drawer'}
        aria-label="Navigation menu"
        aria-hidden={!open}
      >
        <div className="drawer-header">
          <Logo />
          <button
            type="button"
            className="drawer-close"
            aria-label="Close menu"
            onClick={onClose}
          >
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" aria-hidden="true">
              <path
                d="M6 6l12 12M18 6L6 18"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
              />
            </svg>
          </button>
        </div>

        <nav className="drawer-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              onClick={onClose}
              className={({ isActive }) =>
                isActive ? 'drawer-link drawer-link-active' : 'drawer-link'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="drawer-footer">
          <div className="drawer-user">
            <span className="drawer-user-name">
              {user?.name || firebaseUser?.email?.split('@')[0] || t('user.traveler')}
            </span>
            <span className="drawer-user-email">
              {user?.email || firebaseUser?.email || ''}
            </span>
          </div>
          <NavLink to="/profile" onClick={onClose} className="drawer-link">
            {t('user.profile')}
          </NavLink>
          <button type="button" className="drawer-link drawer-logout" onClick={handleLogout}>
            {t('user.logout')}
          </button>
        </div>
      </aside>
    </>
  )
}
