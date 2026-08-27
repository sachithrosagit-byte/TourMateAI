// Read-only star rating with fractional fill (e.g. 4.3 stars). The gold row is
// clipped to `value / 5` of the width over a muted base row.

const STAR_PATH =
  'M12 2.5l2.94 5.95 6.56 0.96-4.75 4.63 1.12 6.54L12 17.5l-5.87 3.08 1.12-6.54L2.5 9.41l6.56-0.96L12 2.5Z'

function StarRow({ size }) {
  return (
    <span className="stars-row">
      {[0, 1, 2, 3, 4].map((i) => (
        <svg key={i} width={size} height={size} viewBox="0 0 24 24" aria-hidden="true">
          <path d={STAR_PATH} fill="currentColor" />
        </svg>
      ))}
    </span>
  )
}

export default function StarRating({ value = 0, size = 15 }) {
  const clamped = Math.max(0, Math.min(5, Number(value) || 0))
  const pct = (clamped / 5) * 100

  return (
    <span className="stars" role="img" aria-label={`Rated ${clamped} out of 5`}>
      <StarRow size={size} />
      <span className="stars-clip" style={{ width: `${pct}%` }}>
        <StarRow size={size} />
      </span>
    </span>
  )
}
