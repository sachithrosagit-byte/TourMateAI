// Route guard: renders children only for authenticated users, otherwise redirects
// to the landing page (remembering where they were headed so login can send
// them back later).

import { Navigate, useLocation } from 'react-router-dom'
import { useAuth } from '../context/AuthContext'

export default function ProtectedRoute({ children }) {
  const { isAuthenticated, loading } = useAuth()
  const location = useLocation()

  // Wait for the first Firebase auth resolution before deciding.
  if (loading) {
    return (
      <div className="loading-screen">
        <div className="spinner" aria-hidden="true" />
        <span>Getting things ready…</span>
      </div>
    )
  }

  if (!isAuthenticated) {
    return <Navigate to="/welcome" replace state={{ from: location }} />
  }

  return children
}
