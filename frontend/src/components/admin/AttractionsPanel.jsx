// Admin › Attractions — the catalogue management table (this is what feeds the
// recommender), with add/edit via modal and a two-step inline delete confirm.

import { useEffect, useMemo, useState } from 'react'
import {
  deleteAttraction,
  fetchAdminAttractions,
} from '../../services/admin'
import AttractionModal from './AttractionModal'

function formatDate(iso) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  })
}

const byName = (a, b) => a.name.localeCompare(b.name)

export default function AttractionsPanel() {
  const [attractions, setAttractions] = useState(null)
  const [loadError, setLoadError] = useState(null)
  const [actionError, setActionError] = useState(null)
  const [search, setSearch] = useState('')
  // modal: null | { attraction: row-or-null }  (null attraction = create)
  const [modal, setModal] = useState(null)
  const [confirmingId, setConfirmingId] = useState(null)
  const [deletingId, setDeletingId] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchAdminAttractions()
      .then((rows) => !cancelled && setAttractions(rows))
      .catch(
        (err) =>
          !cancelled &&
          setLoadError(
            err?.response?.data?.error || 'Could not load attractions.'
          )
      )
    return () => {
      cancelled = true
    }
  }, [])

  const filtered = useMemo(() => {
    if (!attractions) return []
    const term = search.trim().toLowerCase()
    if (!term) return attractions
    return attractions.filter(
      (a) =>
        a.name.toLowerCase().includes(term) ||
        (a.category || '').toLowerCase().includes(term)
    )
  }, [attractions, search])

  const handleSaved = (saved) => {
    setAttractions((rows) => {
      const exists = rows.some((r) => r.id === saved.id)
      const next = exists
        ? rows.map((r) => (r.id === saved.id ? saved : r))
        : [...rows, saved]
      return next.sort(byName)
    })
    setModal(null)
  }

  const handleDelete = async (id) => {
    setDeletingId(id)
    setActionError(null)
    try {
      await deleteAttraction(id)
      setAttractions((rows) => rows.filter((r) => r.id !== id))
    } catch (err) {
      setActionError(
        err?.response?.data?.error || 'Could not delete the attraction.'
      )
    } finally {
      setDeletingId(null)
      setConfirmingId(null)
    }
  }

  if (loadError) {
    return (
      <div className="alert alert-error" role="alert">
        {loadError}
      </div>
    )
  }

  if (!attractions) {
    return (
      <div className="loading-screen">
        <div className="spinner" aria-hidden="true" />
        <span>Loading attractions…</span>
      </div>
    )
  }

  return (
    <>
      <div className="adm-toolbar">
        <input
          className="input"
          type="search"
          placeholder="Search by name or category…"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          aria-label="Search attractions"
        />
        <div className="adm-toolbar-group">
          <span className="adm-count">
            {filtered.length} of {attractions.length}
          </span>
          <button
            type="button"
            className="btn btn-primary"
            onClick={() => setModal({ attraction: null })}
          >
            + Add attraction
          </button>
        </div>
      </div>

      {actionError && (
        <div
          className="alert alert-error"
          role="alert"
          style={{ marginBottom: 'var(--space-4)' }}
        >
          {actionError}
        </div>
      )}

      <div className="card adm-table-wrap">
        {filtered.length === 0 ? (
          <div className="adm-empty">
            {search
              ? 'No attractions match your search.'
              : 'No attractions yet — add the first one.'}
          </div>
        ) : (
          <table className="adm-table">
            <thead>
              <tr>
                <th>Attraction</th>
                <th>Category</th>
                <th className="num">Rating</th>
                <th className="num">Reviews</th>
                <th>Added</th>
                <th aria-label="Actions" />
              </tr>
            </thead>
            <tbody>
              {filtered.map((a) => (
                <tr key={a.id}>
                  <td>
                    <div className="adm-entity">
                      {a.image_url ? (
                        <img
                          className="adm-thumb"
                          src={a.image_url}
                          alt=""
                          loading="lazy"
                        />
                      ) : (
                        <span className="adm-thumb-fallback" aria-hidden="true">
                          {a.name.charAt(0)}
                        </span>
                      )}
                      <div>
                        <div className="adm-cell-main">{a.name}</div>
                        {a.latitude != null && a.longitude != null && (
                          <div className="adm-cell-sub">
                            {a.latitude.toFixed(4)}, {a.longitude.toFixed(4)}
                          </div>
                        )}
                      </div>
                    </div>
                  </td>
                  <td>
                    {a.category ? (
                      <span className="badge">{a.category}</span>
                    ) : (
                      <span className="adm-cell-sub">—</span>
                    )}
                  </td>
                  <td className="num">
                    {a.avg_rating ? `★ ${a.avg_rating.toFixed(1)}` : '—'}
                  </td>
                  <td className="num">{a.review_count ?? 0}</td>
                  <td>{formatDate(a.created_at)}</td>
                  <td>
                    <div className="adm-actions">
                      {confirmingId === a.id ? (
                        <>
                          <span className="adm-confirm-label">Delete?</span>
                          <button
                            type="button"
                            className="btn btn-danger adm-btn-sm"
                            disabled={deletingId === a.id}
                            onClick={() => handleDelete(a.id)}
                          >
                            {deletingId === a.id ? 'Deleting…' : 'Yes, delete'}
                          </button>
                          <button
                            type="button"
                            className="btn btn-secondary adm-btn-sm"
                            onClick={() => setConfirmingId(null)}
                          >
                            Cancel
                          </button>
                        </>
                      ) : (
                        <>
                          <button
                            type="button"
                            className="btn btn-secondary adm-btn-sm"
                            onClick={() => setModal({ attraction: a })}
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            className="btn btn-danger adm-btn-sm"
                            onClick={() => setConfirmingId(a.id)}
                          >
                            Delete
                          </button>
                        </>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        )}
      </div>

      {modal && (
        <AttractionModal
          attraction={modal.attraction}
          onClose={() => setModal(null)}
          onSaved={handleSaved}
        />
      )}
    </>
  )
}
