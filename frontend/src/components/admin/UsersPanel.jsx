// Admin › Users — read-only list of every account with activity counts.
// Admin rights are granted via the backend CLI (flask set-admin), not from here.

import { useEffect, useMemo, useState } from 'react'
import { fetchAdminUsers } from '../../services/admin'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

export default function UsersPanel() {
  const [users, setUsers] = useState(null)
  const [error, setError] = useState(null)
  const [search, setSearch] = useState('')

  useEffect(() => {
    let cancelled = false
    fetchAdminUsers()
      .then((rows) => !cancelled && setUsers(rows))
      .catch(
        (err) =>
          !cancelled &&
          setError(err?.response?.data?.error || 'Could not load users.')
      )
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    if (!users) return []
    const term = search.trim().toLowerCase()
    if (!term) return users
    return users.filter(
      (u) =>
        u.name.toLowerCase().includes(term) ||
        (u.email || '').toLowerCase().includes(term)
    )
  }, [users, search])

  if (error) {
    return (
      <div className="alert alert-error" role="alert">
        {error}
      </div>
    )
  }

  if (!users) {
    return (
      <div className="loading-screen">
        <div className="spinner" aria-hidden="true" />
        <span>Loading users…</span>
      </div>
    )
  }

  return (
    <>
      <div className="adm-toolbar">
        <input
          className="input"
          type="search"
          placeholder="Search by name or email…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search users"
        />
        <span className="adm-count">
          {filtered.length} of {users.length}
        </span>
      </div>

      <div className="card adm-table-wrap">
        {filtered.length === 0 ? (
          <div className="adm-empty">No users match your search.</div>
        ) : (
          <table className="adm-table">
            <thead>
              <tr>
                <th>User</th>
                <th>Role</th>
                <th>Interests</th>
                <th className="num">Interactions</th>
                <th className="num">Reviews</th>
                <th>Joined</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((u) => (
                <tr key={u.id}>
                  <td>
                    <div className="adm-entity">
                      <span className="adm-avatar" aria-hidden="true">
                        {u.name.charAt(0)}
                      </span>
                      <div>
                        <div className="adm-cell-main">{u.name}</div>
                        <div className="adm-cell-sub">{u.email}</div>
                      </div>
                    </div>
                  </td>
                  <td>
                    {u.role === 'admin' ? (
                      <span className="badge badge-primary">Admin</span>
                    ) : (
                      <span className="adm-role-user">Traveler</span>
                    )}
                  </td>
                  <td>
                    {u.preferences?.interests?.length ? (
                      <span className="adm-cell-sub">
                        {u.preferences.interests.join(', ')}
                      </span>
                    ) : (
                      <span className="adm-cell-sub">—</span>
                    )}
                  </td>
                  <td className="num">{u.interactions_count}</td>
                  <td className="num">{u.feedback_count}</td>
                  <td>{formatDate(u.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>
    </>
  )
}
