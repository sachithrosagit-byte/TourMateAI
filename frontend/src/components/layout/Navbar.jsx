// Sticky top navbar: logo, primary nav (desktop), avatar dropdown, and a
// hamburger that opens the mobile drawer. The Admin link only renders for
// admin users.

import { Link, NavLink } from 'react-router-dom'
import useNavItems from '../../hooks/useNavItems'
import Logo from './Logo'
import UserMenu from './UserMenu'

import LanguageSwitcher from './LanguageSwitcher'

export default function Navbar({ onOpenDrawer }) {
  const navItems = useNavItems()

  return (
    <header className="navbar">
      <div className="navbar-inner">
        <button
          type="button"
          className="hamburger"
          aria-label="Open navigation menu"
          onClick={onOpenDrawer}
        >
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path
              d="M4 7h16M4 12h16M4 17h16"
              stroke="currentColor"
              strokeWidth="2"
              strokeLinecap="round"
            />
          </svg>
        </button>

        <Link to="/" className="navbar-brand" aria-label="TourMateAI home">
          <Logo />
        </Link>

        <nav className="navbar-nav" aria-label="Primary">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                isActive ? 'nav-link nav-link-active' : 'nav-link'
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="navbar-end" style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <LanguageSwitcher />
          <UserMenu />
        </div>
      </div>
    </header>
  )
}
