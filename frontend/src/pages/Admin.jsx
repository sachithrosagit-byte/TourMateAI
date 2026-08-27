// Admin dashboard — only for users with role === 'admin' (backend Users.is_admin).
// Everyone else is bounced to the home page; the navbar link is already hidden
// for them (see hooks/useNavItems.js). Three panels behind a segmented tab bar:
// analytics overview, attraction management (CRUD), and the user list.

import { useState } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'
import PageContainer from '../components/layout/PageContainer'
import OverviewPanel from '../components/admin/OverviewPanel'
import AttractionsPanel from '../components/admin/AttractionsPanel'
import UsersPanel from '../components/admin/UsersPanel'
import '../styles/admin.css'

const TABS = [
  { id: 'overview', label: 'Overview' },
  { id: 'attractions', label: 'Attractions' },
  { id: 'users', label: 'Users' },
]

export default function Admin() {
  const { user } = useAuth()
  const [tab, setTab] = useState('overview')

  // ProtectedRoute guarantees auth already resolved; non-admins go home.
  if (user?.role !== 'admin') {
    return <Navigate to="/" replace />
  }

  return (
    <PageContainer
      title="Admin"
      subtitle="Manage the attraction catalogue, users, and see how TourMate is used."
    >
      <div className="adm-tabs" role="tablist" aria-label="Admin sections">
        {TABS.map((t) => (
          <button
            key={t.id}
            type="button"
            role="tab"
            aria-selected={tab === t.id}
            className="adm-tab"
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'overview' && <OverviewPanel />}
      {tab === 'attractions' && <AttractionsPanel />}
      {tab === 'users' && <UsersPanel />}
    </PageContainer>
  )
}
