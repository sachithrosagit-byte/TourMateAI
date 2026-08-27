// Embedded Google Map for an attraction's coordinates. Uses the Google Maps
// Embed API — a plain iframe, so no Maps JS SDK or npm dependency is needed.
//
// Graceful degradation: when no API key is configured (VITE_GOOGLE_MAPS_API_KEY)
// or the attraction has no coordinates, it renders a static location card with a
// link out to Google Maps instead of a broken embed. Either way the page works.

const MAPS_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY

function Fallback({ query, name }) {
  return (
    <div className="map-fallback">
      <span className="map-fallback-pin" aria-hidden="true">
        <svg width="30" height="30" viewBox="0 0 24 24" fill="none">
          <path
            d="M12 21s-6.5-5.4-6.5-10A6.5 6.5 0 0 1 12 4.5 6.5 6.5 0 0 1 18.5 11c0 4.6-6.5 10-6.5 10Z"
            fill="var(--color-primary)"
            stroke="#fff"
            strokeWidth="1.4"
          />
          <circle cx="12" cy="11" r="2.3" fill="#fff" />
        </svg>
      </span>
      {query ? (
        <a
          className="btn btn-secondary map-fallback-link"
          href={`https://www.google.com/maps/search/?api=1&query=${query}`}
          target="_blank"
          rel="noreferrer"
        >
          Open {name} in Google Maps ↗
        </a>
      ) : (
        <span className="map-fallback-note">
          Location coordinates aren’t available for this place yet.
        </span>
      )}
    </div>
  )
}

export default function AttractionMap({ attraction }) {
  const { latitude, longitude, name } = attraction
  const hasCoords =
    typeof latitude === 'number' && typeof longitude === 'number'
  const query = name 
    ? `${name}${attraction.location ? `, ${attraction.location}` : ''}`
    : (hasCoords ? `${latitude},${longitude}` : null)

  // No key (or no coordinates) → static fallback card.
  if (!MAPS_KEY || !hasCoords) {
    return <Fallback query={query} name={name} />
  }

  const src =
    `https://www.google.com/maps/embed/v1/place?key=${MAPS_KEY}` +
    `&q=${encodeURIComponent(query)}&zoom=12`

  return (
    <figure className="detail-map">
      <iframe
        title={`Map showing ${name}`}
        src={src}
        loading="lazy"
        referrerPolicy="no-referrer-when-downgrade"
        allowFullScreen
      />
      <a
        className="detail-map-link"
        href={`https://www.google.com/maps/search/?api=1&query=${query}`}
        target="_blank"
        rel="noreferrer"
      >
        Open in Google Maps ↗
      </a>
    </figure>
  )
}
