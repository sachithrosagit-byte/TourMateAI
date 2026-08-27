// Admin › Overview — headline stat tiles + a "most viewed attractions" bar list.
// Single-series chart: one hue (primary), values at the bar tips in text ink,
// no legend needed (the card title names the series).

import { useEffect, useState } from 'react'
import { fetchAnalytics } from '../../services/admin'

function StatTile({ label, value, note }) {
  return (
    <div className="card adm-stat">
      <div className="adm-stat-label">{label}</div>
      <div className="adm-stat-value">{value}</div>
      {note && <div className="adm-stat-note">{note}</div>}
    </div>
  )
}

export default function OverviewPanel() {
  const [data, setData] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let cancelled = false
    fetchAnalytics()
      .then((d) => !cancelled && setData(d))
      .catch(
        (err) =>
          !cancelled &&
          setError(err?.response?.data?.error || 'Could not load analytics.')
      )
    return () => {
      cancelled = true
    }
  }, [])

  if (error) {
    return (
      <div className="alert alert-error" role="alert">
        {error}
      </div>
    )
  }

  if (!data) {
    return (
      <div className="loading-screen">
        <div className="spinner" aria-hidden="true" />
        <span>Loading analytics…</span>
      </div>
    )
  }

  const { totals, most_viewed: mostViewed } = data
  const maxViews = mostViewed.reduce((max, row) => Math.max(max, row.views), 0)

  return (
    <>
      <div className="adm-stats">
        <StatTile label="Travelers" value={totals.users.toLocaleString()} />
        <StatTile
          label="Attractions"
          value={totals.attractions.toLocaleString()}
        />
        <StatTile
          label="Interactions"
          value={totals.interactions.toLocaleString()}
          note="views, likes & visits"
        />
        <StatTile
          label="Chat messages"
          value={totals.chat_messages.toLocaleString()}
        />
        <StatTile
          label="Avg rating"
          value={
            totals.avg_feedback_rating != null
              ? `${totals.avg_feedback_rating.toFixed(1)} / 5`
              : '—'
          }
          note={`from ${totals.feedback_count.toLocaleString()} review${
            totals.feedback_count === 1 ? '' : 's'
          }`}
        />
      </div>

      <div className="card adm-chart-card">
        <h3 className="adm-chart-title">Most viewed attractions</h3>
        <p className="adm-chart-sub">
          Page views logged when travelers open an attraction.
        </p>

        {mostViewed.length === 0 ? (
          <div className="adm-empty">
            No view data yet — numbers appear once travelers start exploring.
          </div>
        ) : (
          <div className="adm-bars">
            {mostViewed.map((row) => (
              <div
                key={row.attraction_id}
                className="adm-bar-row"
                title={`${row.name} — ${row.views.toLocaleString()} view${
                  row.views === 1 ? '' : 's'
                }`}
              >
                <span className="adm-bar-name">{row.name}</span>
                <span className="adm-bar-track">
                  {/* Width leaves 4.5rem for the tip label so the longest bar
                      can hit "100%" without pushing its value off the row. */}
                  <span
                    className="adm-bar"
                    style={{
                      width: `calc((100% - 4.5rem) * ${
                        maxViews ? row.views / maxViews : 0
                      })`,
                    }}
                    aria-hidden="true"
                  />
                  <span className="adm-bar-value">
                    {row.views.toLocaleString()}
                  </span>
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </>
  )
}
